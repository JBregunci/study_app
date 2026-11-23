from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..db import get_db
from ..models import (
    Exam,
    FeedbackMode,
    Question,
    QuestionSet,
    QuestionSetItem,
    QuizSession,
    ReviewStatus,
    Topic,
)
from ..services import practice
from ..templating import templates
from ..web import parse_feedback_mode, parse_int, parse_limit_seconds, redirect

router = APIRouter()


def _get_set(db: Session, set_id: int) -> QuestionSet:
    question_set = db.get(QuestionSet, set_id)
    if question_set is None:
        raise HTTPException(status_code=404, detail="Conjunto não encontrado")
    return question_set


def _load_questions(db: Session) -> list[Question]:
    return list(
        db.scalars(
            select(Question)
            .options(
                joinedload(Question.topic),
                joinedload(Question.exam),
                selectinload(Question.exams),
            )
            .where(Question.review_status == ReviewStatus.approved)
            .order_by(Question.topic_id, Question.id)
        ).all()
    )


def _load_topics(db: Session) -> list[Topic]:
    return list(
        db.scalars(select(Topic).order_by(Topic.position, Topic.name)).all()
    )


def _load_exams(db: Session) -> list[Exam]:
    return list(db.scalars(select(Exam).order_by(Exam.name)).all())


def _form_context(
    db: Session,
    form: dict,
    selected_ids: set[int],
    question_set: QuestionSet | None,
):
    return {
        "topics": _load_topics(db),
        "exams": _load_exams(db),
        "questions": _load_questions(db),
        "form": form,
        "selected_ids": selected_ids,
        "question_set": question_set,
        "action": f"/conjuntos/{question_set.id}"
        if question_set
        else "/conjuntos/novo",
        "is_edit": question_set is not None,
    }


def _default_form(question_set: QuestionSet | None = None) -> dict:
    if question_set is None:
        return {
            "name": "",
            "description": "",
            "target_title": "",
            "exam_id": "",
            "default_feedback_mode": FeedbackMode.end.value,
            "default_limit_minutes": "",
        }
    limit = question_set.default_limit_seconds
    return {
        "name": question_set.name,
        "description": question_set.description,
        "target_title": question_set.target_title,
        "exam_id": str(question_set.exam_id or ""),
        "default_feedback_mode": question_set.default_feedback_mode.value,
        "default_limit_minutes": str(round(limit / 60, 2)) if limit else "",
    }


def _save_set(
    db: Session,
    question_set: QuestionSet | None,
    name: str,
    description: str,
    target_title: str,
    exam_id: str,
    feedback_mode: str,
    limit_minutes: str,
    question_ids: list[int],
) -> tuple[QuestionSet | None, str | None]:
    name = name.strip()
    if not name:
        return None, "Informe um nome para o conjunto."

    ordered_ids: list[int] = []
    seen: set[int] = set()
    for question_id in question_ids:
        if question_id not in seen:
            seen.add(question_id)
            ordered_ids.append(question_id)
    if not ordered_ids:
        return None, "Selecione pelo menos uma questão."

    questions = {
        question.id: question
        for question in db.scalars(
            select(Question).where(
                Question.id.in_(ordered_ids),
                Question.review_status == ReviewStatus.approved,
            )
        ).all()
    }
    if len(questions) != len(ordered_ids):
        return None, "Uma ou mais questões selecionadas não estão disponíveis."

    parsed_exam_id = parse_int(exam_id)
    exam = None
    if parsed_exam_id is not None:
        exam = db.get(Exam, parsed_exam_id)
        if exam is None:
            return None, "Concurso inválido."

    mode = parse_feedback_mode(feedback_mode, FeedbackMode.end)
    limit = parse_limit_seconds(limit_minutes)

    if question_set is None:
        question_set = QuestionSet()
        db.add(question_set)
    question_set.name = name
    question_set.description = description.strip()
    question_set.target_title = target_title.strip()
    question_set.exam_id = exam.id if exam else None
    question_set.default_feedback_mode = mode
    question_set.default_limit_seconds = limit
    db.flush()

    db.execute(
        delete(QuestionSetItem).where(QuestionSetItem.set_id == question_set.id)
    )
    for position, question_id in enumerate(ordered_ids, start=1):
        db.add(
            QuestionSetItem(
                set_id=question_set.id,
                question_id=question_id,
                position=position,
            )
        )
    db.commit()
    db.refresh(question_set)
    return question_set, None


@router.get("/conjuntos", name="sets_list")
def sets_list(request: Request, db: Session = Depends(get_db)):
    sets = list(
        db.scalars(select(QuestionSet).order_by(QuestionSet.updated_at.desc())).all()
    )
    counts = {item.id: len(item.items) for item in sets}
    return templates.TemplateResponse(
        request=request,
        name="sets/list.html",
        context={"sets": sets, "counts": counts},
    )


@router.get("/conjuntos/novo", name="set_new")
def set_new(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="sets/builder.html",
        context=_form_context(db, _default_form(), set(), None),
    )


@router.post("/conjuntos/novo", name="set_create")
def set_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    description: str = Form(""),
    target_title: str = Form(""),
    exam_id: str = Form(""),
    default_feedback_mode: str = Form("end"),
    default_limit_minutes: str = Form(""),
    question_ids: list[int] = Form(default=[]),
):
    combined, error = _save_set(
        db,
        None,
        name,
        description,
        target_title,
        exam_id,
        default_feedback_mode,
        default_limit_minutes,
        question_ids,
    )
    if error:
        form = {
            "name": name,
            "description": description,
            "target_title": target_title,
            "exam_id": exam_id,
            "default_feedback_mode": default_feedback_mode,
            "default_limit_minutes": default_limit_minutes,
        }
        return templates.TemplateResponse(
            request=request,
            name="sets/builder.html",
            context={**_form_context(db, form, set(question_ids), None), "error": error},
            status_code=400,
        )
    return redirect(
        f"/conjuntos/{combined.id}", msg="Conjunto criado com sucesso."
    )


@router.get("/conjuntos/{set_id}/editar", name="set_edit")
def set_edit(set_id: int, request: Request, db: Session = Depends(get_db)):
    question_set = _get_set(db, set_id)
    selected = {item.question_id for item in question_set.items}
    return templates.TemplateResponse(
        request=request,
        name="sets/builder.html",
        context=_form_context(
            db, _default_form(question_set), selected, question_set
        ),
    )


@router.post("/conjuntos/{set_id}", name="set_update")
def set_update(
    set_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    description: str = Form(""),
    target_title: str = Form(""),
    exam_id: str = Form(""),
    default_feedback_mode: str = Form("end"),
    default_limit_minutes: str = Form(""),
    question_ids: list[int] = Form(default=[]),
):
    question_set = _get_set(db, set_id)
    updated, error = _save_set(
        db,
        question_set,
        name,
        description,
        target_title,
        exam_id,
        default_feedback_mode,
        default_limit_minutes,
        question_ids,
    )
    if error:
        form = {
            "name": name,
            "description": description,
            "target_title": target_title,
            "exam_id": exam_id,
            "default_feedback_mode": default_feedback_mode,
            "default_limit_minutes": default_limit_minutes,
        }
        return templates.TemplateResponse(
            request=request,
            name="sets/builder.html",
            context={**_form_context(db, form, set(question_ids), question_set), "error": error},
            status_code=400,
        )
    return redirect(
        f"/conjuntos/{updated.id}", msg="Conjunto atualizado com sucesso."
    )


@router.get("/conjuntos/{set_id}", name="set_detail")
def set_detail(set_id: int, request: Request, db: Session = Depends(get_db)):
    question_set = _get_set(db, set_id)
    sessions = list(
        db.scalars(
            select(QuizSession)
            .where(QuizSession.set_id == question_set.id)
            .order_by(QuizSession.started_at.desc())
            .limit(5)
        ).all()
    )
    return templates.TemplateResponse(
        request=request,
        name="sets/detail.html",
        context={"question_set": question_set, "sessions": sessions},
    )


@router.post("/conjuntos/{set_id}/excluir", name="set_delete")
def set_delete(set_id: int, db: Session = Depends(get_db)):
    question_set = _get_set(db, set_id)
    db.delete(question_set)
    db.commit()
    return redirect("/conjuntos", msg="Conjunto excluído.")


@router.post("/conjuntos/{set_id}/sessoes", name="set_practice")
def set_practice(
    set_id: int,
    db: Session = Depends(get_db),
    feedback_mode: str = Form(""),
    limit_minutes: str = Form(""),
):
    question_set = _get_set(db, set_id)
    mode = parse_feedback_mode(
        feedback_mode, question_set.default_feedback_mode
    )
    limit = parse_limit_seconds(limit_minutes)
    try:
        session = practice.start_set_session(
            db,
            question_set,
            feedback_mode=mode,
            limit_seconds=limit,
        )
    except ValueError as exc:
        return redirect(f"/conjuntos/{question_set.id}", erro=str(exc))
    return redirect(f"/sessoes/{session.id}")
