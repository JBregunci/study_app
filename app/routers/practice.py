from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import (
    Exam,
    FeedbackMode,
    QuizSession,
    SessionStatus,
    Topic,
)
from ..services import practice, question_bank, stats as stats_service
from ..templating import templates
from ..web import parse_feedback_mode, parse_int, parse_limit_seconds, redirect

router = APIRouter()


def _get_session(db: Session, session_id: int) -> QuizSession:
    session = practice.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return session


def _question_context(db: Session, session: QuizSession, item, error: str | None = None):
    attempt = practice.get_attempt(db, session.id, item.question_id)
    selected_id = attempt.selected_alternative_id if attempt else None
    alternatives = practice.display_alternatives(item.question, selected_id)
    next_pos = practice.next_position(session, item.position)
    return {
        "session": session,
        "item": item,
        "question": item.question,
        "alternatives": alternatives,
        "attempt": attempt,
        "show_feedback": bool(
            attempt and session.feedback_mode == FeedbackMode.immediate
        ),
        "progress": practice.session_progress(db, session),
        "elapsed": practice.elapsed_seconds(item),
        "remaining": practice.remaining_seconds(session, item),
        "next_pos": next_pos,
        "is_last": next_pos is None,
        "error": error,
    }


@router.get("/simulados/aleatorios", name="random_form")
def random_form(request: Request, tema: str = "", db: Session = Depends(get_db)):
    topics = list(
        db.scalars(select(Topic).order_by(Topic.position, Topic.name)).all()
    )
    exams = list(db.scalars(select(Exam).order_by(Exam.name)).all())
    return templates.TemplateResponse(
        request=request,
        name="practice/random_form.html",
        context={"topics": topics, "exams": exams, "selected_topic": tema},
    )


@router.post("/simulados/aleatorios", name="random_start")
def random_start(
    db: Session = Depends(get_db),
    count: str = Form("10"),
    topic_slug: str = Form(""),
    exam_id: str = Form(""),
    feedback_mode: str = Form("end"),
    limit_minutes: str = Form(""),
):
    requested = min(20, max(10, parse_int(count, 10) or 10))
    topic = None
    if topic_slug:
        topic = db.scalar(select(Topic).where(Topic.slug == topic_slug))
        if topic is None:
            return redirect("/simulados/aleatorios", erro="Tema não encontrado.")
    exam = None
    parsed_exam_id = parse_int(exam_id)
    if parsed_exam_id is not None:
        exam = db.get(Exam, parsed_exam_id)
        if exam is None:
            return redirect("/simulados/aleatorios", erro="Concurso não encontrado.")
    mode = parse_feedback_mode(feedback_mode, FeedbackMode.end)
    limit = parse_limit_seconds(limit_minutes)
    topic_ids = (
        question_bank.descendant_topic_ids(db, topic.slug) if topic else None
    )
    try:
        session = practice.start_random_session(
            db,
            count=requested,
            feedback_mode=mode,
            limit_seconds=limit,
            topic=topic,
            exam_id=exam.id if exam else None,
            topic_ids=topic_ids,
        )
    except ValueError as exc:
        return redirect("/simulados/aleatorios", erro=str(exc))
    if session.total_planned < requested:
        return redirect(
            f"/sessoes/{session.id}",
            msg=(
                f"Existiam apenas {session.total_planned} questões aprovadas "
                "para os filtros escolhidos."
            ),
        )
    return redirect(f"/sessoes/{session.id}")


@router.get("/sessoes/{session_id}", name="session_resume")
def session_resume(session_id: int, db: Session = Depends(get_db)):
    session = _get_session(db, session_id)
    if session.status == SessionStatus.abandoned:
        return redirect("/", erro="Esta sessão foi abandonada.")
    if session.status == SessionStatus.completed:
        return redirect(f"/sessoes/{session.id}/resultado")
    item = practice.current_item(db, session)
    if item is None:
        practice.finish_session(db, session)
        return redirect(f"/sessoes/{session.id}/resultado")
    return redirect(f"/sessoes/{session.id}/questoes/{item.position}")


@router.get(
    "/sessoes/{session_id}/questoes/{position}",
    name="question_view",
    response_class=HTMLResponse,
)
def question_view(
    session_id: int,
    position: int,
    request: Request,
    db: Session = Depends(get_db),
):
    session = _get_session(db, session_id)
    if session.status == SessionStatus.abandoned:
        return redirect("/", erro="Esta sessão foi abandonada.")
    if session.status == SessionStatus.completed:
        return redirect(f"/sessoes/{session.id}/resultado")
    item = practice.get_item(db, session, position)
    if item is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    practice.ensure_shown(db, item)
    practice.record_timeout_if_needed(db, session, item)
    context = _question_context(db, session, item)
    return templates.TemplateResponse(
        request=request, name="practice/question.html", context=context
    )


@router.post(
    "/sessoes/{session_id}/questoes/{position}/resposta",
    name="answer_question",
    response_class=HTMLResponse,
)
def answer_question(
    session_id: int,
    position: int,
    request: Request,
    db: Session = Depends(get_db),
    alternative_id: str = Form(""),
    timed_out: str = Form("0"),
):
    session = _get_session(db, session_id)
    if session.status == SessionStatus.abandoned:
        return redirect("/", erro="Esta sessão foi abandonada.")
    item = practice.get_item(db, session, position)
    if item is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada")

    is_htmx = request.headers.get("HX-Request", "").lower() == "true"
    error = None
    if session.status == SessionStatus.completed:
        attempt = practice.get_attempt(db, session.id, item.question_id)
        if attempt is None:
            return redirect(f"/sessoes/{session.id}/resultado")
    else:
        practice.ensure_shown(db, item)
        try:
            practice.record_answer(
                db,
                session,
                item,
                parse_int(alternative_id),
                force_timeout=timed_out == "1",
            )
        except ValueError as exc:
            error = str(exc)

    context = _question_context(db, session, item, error=error)
    if is_htmx:
        return templates.TemplateResponse(
            request=request,
            name="partials/question_body.html",
            context=context,
        )
    if error:
        return redirect(
            f"/sessoes/{session.id}/questoes/{item.position}", erro=error
        )
    return redirect(f"/sessoes/{session.id}/questoes/{item.position}")


@router.post("/sessoes/{session_id}/encerrar", name="finish_session")
def finish_session(session_id: int, db: Session = Depends(get_db)):
    session = _get_session(db, session_id)
    if session.status == SessionStatus.abandoned:
        return redirect("/", erro="Esta sessão foi abandonada.")
    practice.finish_session(db, session)
    return redirect(f"/sessoes/{session.id}/resultado")


@router.get("/sessoes/{session_id}/resultado", name="session_result")
def session_result(
    session_id: int, request: Request, db: Session = Depends(get_db)
):
    session = _get_session(db, session_id)
    if session.status == SessionStatus.abandoned:
        return redirect("/", erro="Esta sessão foi abandonada.")
    if session.status == SessionStatus.in_progress:
        return redirect(
            f"/sessoes/{session.id}",
            erro="Encerre a sessão para visualizar o resultado.",
        )
    result = practice.session_result(db, session)
    session_questions = [row.item.question for row in result["rows"]]
    materials = question_bank.recommended_materials_for_session(
        db, session_questions
    )
    return templates.TemplateResponse(
        request=request,
        name="practice/result.html",
        context={
            "session": session,
            "result": result,
            "breakdown": stats_service.session_breakdown(db, session.id),
            "materials": materials,
        },
    )
