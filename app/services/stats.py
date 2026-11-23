from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..models import (
    question_exams,
    Alternative,
    Attempt,
    Question,
    QuizSession,
    ReviewStatus,
    Tag,
    Topic,
)
from ..utils import local_today
from .practice import correct_alternative, display_alternatives


@dataclass
class Stats:
    total: int = 0
    correct: int = 0
    blank: int = 0
    total_seconds: int = 0

    @property
    def incorrect(self) -> int:
        return max(0, self.total - self.correct - self.blank)

    @property
    def accuracy(self) -> float | None:
        if not self.total:
            return None
        return self.correct * 100 / self.total

    @property
    def avg_seconds(self) -> float | None:
        if not self.total:
            return None
        return self.total_seconds / self.total


@dataclass
class DailyStats(Stats):
    day: date | None = None


@dataclass
class TopicStats:
    topic: Topic
    stats: Stats


@dataclass
class TagStats:
    tag: Tag
    stats: Stats


@dataclass
class AreaStats:
    area: str
    stats: Stats


@dataclass
class SessionSummary:
    session: QuizSession
    answered: int
    correct: int
    total_seconds: int

    @property
    def accuracy(self) -> float | None:
        if not self.answered:
            return None
        return self.correct * 100 / self.answered


@dataclass
class WrongAttempt:
    attempt: Attempt
    question: Question
    topic: Topic
    selected: Alternative | None
    correct: Alternative | None
    alternatives: list[Alternative]
    latest_retry: Attempt | None = None
    retry_status: str = "unresolved"
    resolved_at: datetime | None = None


def _base_counts():
    return (
        func.count(Attempt.id),
        func.coalesce(
            func.sum(case((Attempt.is_correct.is_(True), 1), else_=0)), 0
        ),
        func.coalesce(
            func.sum(
                case((Attempt.selected_alternative_id.is_(None), 1), else_=0)
            ),
            0,
        ),
        func.coalesce(func.sum(Attempt.time_spent_seconds), 0),
    )


def stats_for_period(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    topic_id: int | None = None,
    exam_id: int | None = None,
    topic_ids: set[int] | None = None,
) -> Stats:
    total, correct, blank, total_seconds = _base_counts()
    stmt = select(total, correct, blank, total_seconds).select_from(Attempt)
    needs_question = topic_id is not None or topic_ids is not None
    if needs_question:
        stmt = stmt.join(Question, Attempt.question_id == Question.id)
    if topic_id is not None:
        stmt = stmt.where(Question.topic_id == topic_id)
    elif topic_ids is not None:
        stmt = stmt.where(Question.topic_id.in_(topic_ids))
    if exam_id is not None:
        stmt = stmt.where(
            Attempt.question_id.in_(
                select(question_exams.c.question_id).where(
                    question_exams.c.exam_id == exam_id
                )
            )
        )
    if start is not None:
        stmt = stmt.where(Attempt.answered_on >= start)
    if end is not None:
        stmt = stmt.where(Attempt.answered_on <= end)
    row = db.execute(stmt).one()
    return Stats(
        total=int(row[0] or 0),
        correct=int(row[1] or 0),
        blank=int(row[2] or 0),
        total_seconds=int(row[3] or 0),
    )


def stats_for_day(db: Session, day: date | None = None) -> Stats:
    target = day or local_today()
    return stats_for_period(db, start=target, end=target)


def daily_series(db: Session, days: int = 14) -> list[DailyStats]:
    days = max(1, days)
    end = local_today()
    start = end - timedelta(days=days - 1)
    total, correct, blank, total_seconds = _base_counts()
    rows = db.execute(
        select(Attempt.answered_on, total, correct, blank, total_seconds)
        .where(Attempt.answered_on >= start, Attempt.answered_on <= end)
        .group_by(Attempt.answered_on)
        .order_by(Attempt.answered_on)
    ).all()
    by_day = {
        row[0]: Stats(
            total=int(row[1] or 0),
            correct=int(row[2] or 0),
            blank=int(row[3] or 0),
            total_seconds=int(row[4] or 0),
        )
        for row in rows
    }
    series = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        stats = by_day.get(day, Stats())
        series.append(
            DailyStats(
                day=day,
                total=stats.total,
                correct=stats.correct,
                blank=stats.blank,
                total_seconds=stats.total_seconds,
            )
        )
    return series


def topic_stats(
    db: Session, start: date | None = None, end: date | None = None
) -> list[TopicStats]:
    total, correct, blank, total_seconds = _base_counts()
    stmt = (
        select(
            Question.topic_id,
            total,
            correct,
            blank,
            total_seconds,
        )
        .select_from(Attempt)
        .join(Question, Attempt.question_id == Question.id)
        .group_by(Question.topic_id)
    )
    if start is not None:
        stmt = stmt.where(Attempt.answered_on >= start)
    if end is not None:
        stmt = stmt.where(Attempt.answered_on <= end)
    rows = db.execute(stmt).all()
    by_topic = {
        row[0]: Stats(
            total=int(row[1] or 0),
            correct=int(row[2] or 0),
            blank=int(row[3] or 0),
            total_seconds=int(row[4] or 0),
        )
        for row in rows
    }
    topics = list(
        db.scalars(select(Topic).order_by(Topic.position, Topic.name)).all()
    )
    return [TopicStats(topic=topic, stats=by_topic.get(topic.id, Stats())) for topic in topics]


def tag_stats(
    db: Session, start: date | None = None, end: date | None = None
) -> list[TagStats]:
    total, correct, blank, total_seconds = _base_counts()
    stmt = (
        select(
            Tag,
            total,
            correct,
            blank,
            total_seconds,
        )
        .select_from(Attempt)
        .join(Question, Attempt.question_id == Question.id)
        .join(Tag, Question.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(Tag.area, Tag.position, Tag.name)
    )
    if start is not None:
        stmt = stmt.where(Attempt.answered_on >= start)
    if end is not None:
        stmt = stmt.where(Attempt.answered_on <= end)
    rows = db.execute(stmt).all()
    return [
        TagStats(
            tag=row[0],
            stats=Stats(
                total=int(row[1] or 0),
                correct=int(row[2] or 0),
                blank=int(row[3] or 0),
                total_seconds=int(row[4] or 0),
            ),
        )
        for row in rows
    ]


def area_stats(
    db: Session, start: date | None = None, end: date | None = None
) -> list[AreaStats]:
    total, correct, blank, total_seconds = _base_counts()
    stmt = (
        select(
            Tag.area,
            total,
            correct,
            blank,
            total_seconds,
        )
        .select_from(Attempt)
        .join(Question, Attempt.question_id == Question.id)
        .join(Tag, Question.tag_id == Tag.id)
        .group_by(Tag.area)
        .order_by(Tag.area)
    )
    if start is not None:
        stmt = stmt.where(Attempt.answered_on >= start)
    if end is not None:
        stmt = stmt.where(Attempt.answered_on <= end)
    rows = db.execute(stmt).all()
    return [
        AreaStats(
            area=row[0],
            stats=Stats(
                total=int(row[1] or 0),
                correct=int(row[2] or 0),
                blank=int(row[3] or 0),
                total_seconds=int(row[4] or 0),
            ),
        )
        for row in rows
    ]


def approved_counts_by_topic(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(Question.topic_id, func.count(Question.id))
        .where(Question.review_status == ReviewStatus.approved)
        .group_by(Question.topic_id)
    ).all()
    return {row[0]: int(row[1]) for row in rows}


def streak(db: Session) -> int:
    dates = list(
        db.scalars(
            select(Attempt.answered_on)
            .distinct()
            .order_by(Attempt.answered_on.desc())
        ).all()
    )
    if not dates:
        return 0
    today = local_today()
    latest = dates[0]
    if latest not in {today, today - timedelta(days=1)}:
        return 0
    count = 1
    expected = latest - timedelta(days=1)
    for answered_on in dates[1:]:
        if answered_on != expected:
            break
        count += 1
        expected -= timedelta(days=1)
    return count


def session_summaries(
    db: Session, limit: int = 8, status=None
) -> list[SessionSummary]:
    count = func.count(Attempt.id)
    correct = func.coalesce(
        func.sum(case((Attempt.is_correct.is_(True), 1), else_=0)), 0
    )
    seconds = func.coalesce(func.sum(Attempt.time_spent_seconds), 0)
    stmt = (
        select(QuizSession, count, correct, seconds)
        .outerjoin(Attempt, Attempt.session_id == QuizSession.id)
        .group_by(QuizSession.id)
        .order_by(QuizSession.started_at.desc())
        .limit(limit)
    )
    if status is not None:
        stmt = stmt.where(QuizSession.status == status)
    rows = db.execute(stmt).all()
    return [
        SessionSummary(
            session=row[0],
            answered=int(row[1] or 0),
            correct=int(row[2] or 0),
            total_seconds=int(row[3] or 0),
        )
        for row in rows
    ]


def recent_wrong_attempts(
    db: Session,
    limit: int = 12,
    start: date | None = None,
    include_resolved: bool = True,
) -> list[WrongAttempt]:
    latest_wrong = (
        select(
            Attempt.question_id.label("question_id"),
            func.max(Attempt.id).label("attempt_id"),
        )
        .where(Attempt.is_correct.is_(False))
        .group_by(Attempt.question_id)
        .subquery()
    )
    stmt = (
        select(Attempt)
        .join(latest_wrong, Attempt.id == latest_wrong.c.attempt_id)
        .options(
            joinedload(Attempt.selected_alternative),
            selectinload(Attempt.question).selectinload(Question.topic),
            selectinload(Attempt.question).selectinload(Question.alternatives),
        )
        .order_by(Attempt.answered_at.desc(), Attempt.id.desc())
    )
    if start is not None:
        stmt = stmt.where(Attempt.answered_on >= start)
    attempts = list(db.scalars(stmt).all())
    results = []
    for attempt in attempts:
        selected = attempt.selected_alternative
        question = attempt.question
        latest_retry = db.scalar(
            select(Attempt)
            .where(
                Attempt.question_id == attempt.question_id,
                Attempt.id > attempt.id,
            )
            .order_by(Attempt.answered_at.desc(), Attempt.id.desc())
            .limit(1)
        )
        retry_status = "unresolved"
        resolved_at = None
        if latest_retry is not None:
            if latest_retry.is_correct:
                retry_status = "resolved"
                resolved_at = latest_retry.answered_at
            else:
                retry_status = "still_wrong"
        if retry_status == "resolved" and not include_resolved:
            continue
        results.append(
            WrongAttempt(
                attempt=attempt,
                question=question,
                topic=question.topic,
                selected=selected,
                correct=correct_alternative(question),
                alternatives=display_alternatives(
                    question, selected.id if selected else None
                ),
                latest_retry=latest_retry,
                retry_status=retry_status,
                resolved_at=resolved_at,
            )
        )
    return results[:limit]


def session_topic_stats(db: Session, session_id: int) -> list[TopicStats]:
    total, correct, blank, total_seconds = _base_counts()
    rows = db.execute(
        select(
            Question.topic_id,
            total,
            correct,
            blank,
            total_seconds,
        )
        .select_from(Attempt)
        .join(Question, Attempt.question_id == Question.id)
        .where(Attempt.session_id == session_id)
        .group_by(Question.topic_id)
    ).all()
    if not rows:
        return []
    topic_ids = [row[0] for row in rows]
    topics = {
        topic.id: topic
        for topic in db.scalars(select(Topic).where(Topic.id.in_(topic_ids))).all()
    }
    return [
        TopicStats(
            topic=topics[row[0]],
            stats=Stats(
                total=int(row[1] or 0),
                correct=int(row[2] or 0),
                blank=int(row[3] or 0),
                total_seconds=int(row[4] or 0),
            ),
        )
        for row in rows
        if row[0] in topics
    ]


def session_breakdown(db: Session, session_id: int) -> dict:
    rows = session_topic_stats(db, session_id)
    valid = [row for row in rows if row.stats.total > 0]
    best = max(valid, key=lambda row: (row.stats.accuracy or 0, row.stats.correct), default=None)
    worst = min(valid, key=lambda row: (row.stats.accuracy or 0, -row.stats.correct), default=None)

    type_rows = db.execute(
        select(
            Question.type,
            func.count(Attempt.id),
            func.coalesce(
                func.sum(case((Attempt.is_correct.is_(True), 1), else_=0)), 0
            ),
            func.coalesce(
                func.sum(
                    case((Attempt.selected_alternative_id.is_(None), 1), else_=0)
                ),
                0,
            ),
            func.coalesce(func.sum(Attempt.time_spent_seconds), 0),
        )
        .select_from(Attempt)
        .join(Question, Attempt.question_id == Question.id)
        .where(Attempt.session_id == session_id)
        .group_by(Question.type)
    ).all()
    type_stats = [
        {
            "label": "Certo/Errado" if row[0].value == "true_false" else "Múltipla escolha",
            "stats": Stats(
                total=int(row[1] or 0),
                correct=int(row[2] or 0),
                blank=int(row[3] or 0),
                total_seconds=int(row[4] or 0),
            ),
        }
        for row in type_rows
    ]
    return {
        "topics": sorted(rows, key=lambda row: row.topic.name),
        "best": best,
        "worst": worst,
        "types": type_stats,
    }
