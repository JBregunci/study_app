from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Alternative,
    Attempt,
    FeedbackMode,
    Question,
    QuestionSet,
    QuestionSetItem,
    QuizSession,
    ReviewStatus,
    SessionItem,
    SessionMode,
    SessionStatus,
    Topic,
)
from ..utils import local_today, utc_now


def _approved_questions_query():
    return select(Question).where(Question.review_status == ReviewStatus.approved)


def get_question_count(
    db: Session,
    topic_id: int | None = None,
    topic_ids: set[int] | None = None,
) -> int:
    stmt = select(func.count(Question.id)).where(
        Question.review_status == ReviewStatus.approved
    )
    if topic_ids is not None:
        stmt = stmt.where(Question.topic_id.in_(topic_ids))
    elif topic_id is not None:
        stmt = stmt.where(Question.topic_id == topic_id)
    return int(db.scalar(stmt) or 0)


def _create_session(
    db: Session,
    title: str,
    mode: SessionMode,
    questions: list[Question],
    feedback_mode: FeedbackMode,
    limit_seconds: int | None,
    topic_id: int | None = None,
    set_id: int | None = None,
) -> QuizSession:
    session = QuizSession(
        title=title,
        mode=mode,
        topic_id=topic_id,
        set_id=set_id,
        feedback_mode=feedback_mode,
        per_question_limit_seconds=limit_seconds,
        status=SessionStatus.in_progress,
        total_planned=len(questions),
    )
    db.add(session)
    db.flush()
    for position, question in enumerate(questions, start=1):
        db.add(
            SessionItem(
                session_id=session.id,
                question_id=question.id,
                position=position,
            )
        )
    db.commit()
    db.refresh(session)
    return session


def get_in_progress_sequential(db: Session, topic_id: int) -> QuizSession | None:
    return db.scalar(
        select(QuizSession)
        .where(
            QuizSession.topic_id == topic_id,
            QuizSession.mode == SessionMode.sequential,
            QuizSession.status == SessionStatus.in_progress,
        )
        .order_by(QuizSession.started_at.desc())
    )


def start_sequential_session(
    db: Session,
    topic: Topic,
    feedback_mode: FeedbackMode,
    limit_seconds: int | None,
    restart: bool = False,
    topic_ids: set[int] | None = None,
) -> QuizSession:
    existing = get_in_progress_sequential(db, topic.id)
    if existing is not None and not restart:
        return existing
    if existing is not None:
        existing.status = SessionStatus.abandoned
        existing.finished_at = utc_now()
        db.commit()

    topic_filter = topic_ids if topic_ids is not None else {topic.id}
    questions = list(
        db.scalars(
            _approved_questions_query()
            .where(Question.topic_id.in_(topic_filter))
            .order_by(Question.id)
        ).all()
    )
    if not questions:
        raise ValueError("Este tema ainda não possui questões aprovadas.")
    return _create_session(
        db,
        title=f"Prática — {topic.name}",
        mode=SessionMode.sequential,
        questions=questions,
        feedback_mode=feedback_mode,
        limit_seconds=limit_seconds,
        topic_id=topic.id,
    )


def start_random_session(
    db: Session,
    count: int,
    feedback_mode: FeedbackMode,
    limit_seconds: int | None,
    topic: Topic | None = None,
    exam_id: int | None = None,
    topic_ids: set[int] | None = None,
) -> QuizSession:
    stmt = _approved_questions_query()
    if topic_ids is not None:
        stmt = stmt.where(Question.topic_id.in_(topic_ids))
    elif topic is not None:
        stmt = stmt.where(Question.topic_id == topic.id)
    if exam_id is not None:
        stmt = stmt.where(Question.exam_id == exam_id)
    stmt = stmt.order_by(func.random()).limit(count)
    questions = list(db.scalars(stmt).all())
    if not questions:
        raise ValueError("Não há questões aprovadas para os filtros escolhidos.")

    title_parts = ["Simulado aleatório"]
    if topic is not None:
        title_parts.append(topic.name)
    title = " — ".join(title_parts) + f" ({len(questions)} questões)"
    return _create_session(
        db,
        title=title,
        mode=SessionMode.random,
        questions=questions,
        feedback_mode=feedback_mode,
        limit_seconds=limit_seconds,
        topic_id=topic.id if topic else None,
    )


def start_set_session(
    db: Session,
    question_set: QuestionSet,
    feedback_mode: FeedbackMode,
    limit_seconds: int | None,
) -> QuizSession:
    questions = list(
        db.scalars(
            select(Question)
            .join(QuestionSetItem, QuestionSetItem.question_id == Question.id)
            .where(
                QuestionSetItem.set_id == question_set.id,
                Question.review_status == ReviewStatus.approved,
            )
            .order_by(QuestionSetItem.position)
        ).all()
    )
    if not questions:
        raise ValueError("Este conjunto não possui questões aprovadas disponíveis.")
    return _create_session(
        db,
        title=f"Simulado — {question_set.name}",
        mode=SessionMode.set,
        questions=questions,
        feedback_mode=feedback_mode,
        limit_seconds=limit_seconds,
        set_id=question_set.id,
    )


def start_retry_session(db: Session, question: Question) -> QuizSession:
    if question.review_status != ReviewStatus.approved:
        raise ValueError("Esta questão não está disponível para prática.")
    return _create_session(
        db,
        title=f"Revisão — {question.external_id}",
        mode=SessionMode.retry,
        questions=[question],
        feedback_mode=FeedbackMode.immediate,
        limit_seconds=None,
        topic_id=question.topic_id,
    )


def get_session(db: Session, session_id: int) -> QuizSession | None:
    return db.get(QuizSession, session_id)


def get_item(db: Session, session: QuizSession, position: int) -> SessionItem | None:
    return db.scalar(
        select(SessionItem).where(
            SessionItem.session_id == session.id,
            SessionItem.position == position,
        )
    )


def get_attempt(db: Session, session_id: int, question_id: int) -> Attempt | None:
    return db.scalar(
        select(Attempt).where(
            Attempt.session_id == session_id,
            Attempt.question_id == question_id,
        )
    )


def answered_question_ids(db: Session, session_id: int) -> set[int]:
    return set(
        db.scalars(
            select(Attempt.question_id).where(Attempt.session_id == session_id)
        ).all()
    )


def current_item(db: Session, session: QuizSession) -> SessionItem | None:
    answered = answered_question_ids(db, session.id)
    for item in session.items:
        if item.question_id not in answered:
            return item
    return None


def ensure_shown(db: Session, item: SessionItem) -> None:
    if item.shown_at is None:
        item.shown_at = utc_now()
        db.commit()
        db.refresh(item)


def elapsed_seconds(item: SessionItem) -> int:
    if item.shown_at is None:
        return 0
    delta = utc_now() - item.shown_at
    return max(0, int(delta.total_seconds()))


def remaining_seconds(session: QuizSession, item: SessionItem) -> int | None:
    if session.per_question_limit_seconds is None:
        return None
    return max(0, session.per_question_limit_seconds - elapsed_seconds(item))


def _complete_if_finished(db: Session, session: QuizSession) -> None:
    answered = db.scalar(
        select(func.count(Attempt.id)).where(Attempt.session_id == session.id)
    )
    if answered and int(answered) >= session.total_planned:
        session.status = SessionStatus.completed
        session.finished_at = utc_now()
        db.commit()


def record_answer(
    db: Session,
    session: QuizSession,
    item: SessionItem,
    alternative_id: int | None,
    force_timeout: bool = False,
) -> Attempt:
    existing = get_attempt(db, session.id, item.question_id)
    if existing is not None:
        return existing
    if session.status != SessionStatus.in_progress:
        raise ValueError("Esta sessão já foi encerrada.")

    elapsed = elapsed_seconds(item)
    limit = session.per_question_limit_seconds
    timed_out = force_timeout or (limit is not None and elapsed >= limit)

    if not timed_out and alternative_id is None:
        raise ValueError("Selecione uma alternativa.")

    alternative = None
    if not timed_out and alternative_id is not None:
        alternative = db.get(Alternative, alternative_id)
        if (
            alternative is None
            or alternative.question_id != item.question_id
            or not alternative.is_active
        ):
            raise ValueError("Selecione uma alternativa válida.")

    is_correct = bool(alternative and alternative.is_correct)
    attempt = Attempt(
        session_id=session.id,
        question_id=item.question_id,
        selected_alternative_id=alternative.id if alternative else None,
        is_correct=is_correct,
        timed_out=timed_out,
        time_spent_seconds=elapsed,
        answered_at=utc_now(),
        answered_on=local_today(),
    )
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = get_attempt(db, session.id, item.question_id)
        if existing is not None:
            return existing
        raise
    db.refresh(attempt)
    _complete_if_finished(db, session)
    return attempt


def record_timeout_if_needed(
    db: Session, session: QuizSession, item: SessionItem
) -> Attempt | None:
    existing = get_attempt(db, session.id, item.question_id)
    if existing is not None:
        return existing
    if session.status != SessionStatus.in_progress:
        return None
    limit = session.per_question_limit_seconds
    if limit is None:
        return None
    if elapsed_seconds(item) < limit:
        return None
    return record_answer(db, session, item, None, force_timeout=True)


def finish_session(db: Session, session: QuizSession) -> None:
    if session.status == SessionStatus.in_progress:
        session.status = SessionStatus.completed
        session.finished_at = utc_now()
        db.commit()


def display_alternatives(
    question: Question, selected_id: int | None = None
) -> list[Alternative]:
    alternatives = [
        alternative
        for alternative in question.alternatives
        if alternative.is_active or alternative.id == selected_id
    ]
    return sorted(alternatives, key=lambda alternative: alternative.position)


def correct_alternative(question: Question) -> Alternative | None:
    for alternative in question.alternatives:
        if alternative.is_active and alternative.is_correct:
            return alternative
    return None


def session_progress(db: Session, session: QuizSession) -> dict:
    attempts = list(
        db.scalars(
            select(Attempt)
            .where(Attempt.session_id == session.id)
            .order_by(Attempt.id)
        ).all()
    )
    correct = sum(1 for attempt in attempts if attempt.is_correct)
    total_time = sum(attempt.time_spent_seconds for attempt in attempts)
    return {
        "answered": len(attempts),
        "correct": correct,
        "incorrect": len(attempts) - correct,
        "total": session.total_planned,
        "total_time": total_time,
        "percent": round(len(attempts) * 100 / session.total_planned)
        if session.total_planned
        else 0,
    }


@dataclass
class ReviewRow:
    item: SessionItem
    attempt: Attempt | None
    selected: Alternative | None
    correct: Alternative | None
    alternatives: list[Alternative]


def session_result(db: Session, session: QuizSession) -> dict:
    attempts = {
        attempt.question_id: attempt
        for attempt in db.scalars(
            select(Attempt).where(Attempt.session_id == session.id)
        ).all()
    }
    rows: list[ReviewRow] = []
    for item in session.items:
        attempt = attempts.get(item.question_id)
        selected = None
        if attempt is not None and attempt.selected_alternative_id is not None:
            selected = db.get(Alternative, attempt.selected_alternative_id)
        correct = correct_alternative(item.question)
        alternatives = display_alternatives(
            item.question, selected.id if selected else None
        )
        rows.append(
            ReviewRow(
                item=item,
                attempt=attempt,
                selected=selected,
                correct=correct,
                alternatives=alternatives,
            )
        )

    answered = sum(1 for attempt in attempts.values())
    correct_count = sum(1 for attempt in attempts.values() if attempt.is_correct)
    total_time = sum(attempt.time_spent_seconds for attempt in attempts.values())
    return {
        "rows": rows,
        "answered": answered,
        "correct": correct_count,
        "incorrect": answered - correct_count,
        "blank": session.total_planned - answered,
        "total": session.total_planned,
        "total_time": total_time,
        "average_time": round(total_time / answered) if answered else None,
        "accuracy": round(correct_count * 100 / answered) if answered else None,
    }



def next_position(session: QuizSession, current_position: int) -> int | None:
    for item in session.items:
        if item.position > current_position:
            return item.position
    return None



def in_progress_sessions(db: Session) -> list[QuizSession]:
    return list(
        db.scalars(
            select(QuizSession)
            .where(QuizSession.status == SessionStatus.in_progress)
            .order_by(QuizSession.started_at.desc())
        ).all()
    )
