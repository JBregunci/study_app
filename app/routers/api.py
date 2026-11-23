from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..config import APP_NAME
from ..db import get_db
from ..models import Exam, Question, ReviewStatus, Topic
from ..schemas import QuestionFile
from ..services.question_import import import_payload

router = APIRouter(prefix="/api")


def _serialize(question: Question) -> dict:
    return {
        "external_id": question.external_id,
        "type": question.type.value,
        "topic": question.topic.slug,
        "exam": question.exam.slug if question.exam else None,
        "statement": question.statement,
        "context": question.context,
        "media_url": question.media_url,
        "context_media_url": question.context_media_url,
        "difficulty": question.difficulty.value if question.difficulty else None,
        "source": question.source,
        "source_url": question.source_url,
        "source_question_number": question.source_question_number,
        "general_explanation": question.general_explanation,
        "tag": {
            "slug": question.tag.slug,
            "name": question.tag.name,
            "area": question.tag.area,
        },
        "origin": question.origin.value,
        "answer_source": question.answer_source.value,
        "explanation_source": question.explanation_source.value,
        "review_status": question.review_status.value,
        "exam_details": {
            "name": question.exam.name,
            "organization": question.exam.organization,
            "agency": question.exam.agency,
            "contest_key": question.exam.contest_key,
            "year": question.exam.year,
            "role": question.exam.role,
        } if question.exam else None,
        "exams": [
            {
                "slug": exam.slug,
                "name": exam.name,
                "organization": exam.organization,
                "agency": exam.agency,
                "contest_key": exam.contest_key,
                "year": exam.year,
                "role": exam.role,
            }
            for exam in question.exams
        ],
        "alternatives": [
            {
                "label": alternative.label,
                "text": alternative.text,
                "is_correct": alternative.is_correct,
                "explanation": alternative.explanation,
                "media_url": alternative.media_url,
            }
            for alternative in sorted(
                question.alternatives, key=lambda item: item.position
            )
            if alternative.is_active
        ],
    }


@router.get("/health")
def health(db: Session = Depends(get_db)):
    return {
        "app": APP_NAME,
        "status": "ok",
        "questions": int(
            db.scalar(select(func.count(Question.id))) or 0
        ),
    }


@router.get("/questions")
def list_questions(
    db: Session = Depends(get_db),
    topic: str | None = None,
    exam: str | None = None,
    status: str = Query("approved"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(Question).options(
        joinedload(Question.topic),
        joinedload(Question.exam),
        selectinload(Question.alternatives),
        joinedload(Question.tag),
        selectinload(Question.exams),
    )
    if topic:
        stmt = stmt.join(Topic, Question.topic_id == Topic.id).where(
            Topic.slug == topic
        )
    if exam:
        stmt = stmt.where(Question.exams.any(Exam.slug == exam))
    if status != "all":
        try:
            stmt = stmt.where(Question.review_status == ReviewStatus(status))
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail="Status inválido."
            ) from exc
    stmt = stmt.order_by(Question.id).limit(limit).offset(offset)
    questions = list(db.scalars(stmt).unique().all())
    return {"count": len(questions), "questions": [_serialize(q) for q in questions]}


@router.get("/questions/{external_id}")
def get_question(external_id: str, db: Session = Depends(get_db)):
    question = db.scalar(
        select(Question)
        .options(
            joinedload(Question.topic),
            joinedload(Question.exam),
            selectinload(Question.alternatives),
            joinedload(Question.tag),
            selectinload(Question.exams),
        )
        .where(Question.external_id == external_id)
    )
    if question is None:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    return _serialize(question)


@router.post("/questions/import")
def import_questions(payload: QuestionFile, db: Session = Depends(get_db)):
    report = import_payload(
        db, payload, default_status=ReviewStatus.draft, source_name="API"
    )
    return report.to_dict()
