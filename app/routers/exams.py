from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Exam
from ..services import question_bank, stats
from ..templating import templates

router = APIRouter()


@router.get("/concursos", name="exams_list")
def exams_list(request: Request, db: Session = Depends(get_db)):
    rows = []
    for item in question_bank.exam_rows(db):
        exam = item["exam"]
        rows.append(
            {
                "exam": exam,
                "total": item["total"],
                "stats": stats.stats_for_period(db, exam_id=exam.id),
            }
        )
    return templates.TemplateResponse(
        request=request, name="exams/list.html", context={"rows": rows}
    )


@router.get("/concursos/{slug}", name="exam_detail")
def exam_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    exam = db.scalar(select(Exam).where(Exam.slug == slug))
    if exam is None:
        raise HTTPException(status_code=404, detail="Concurso não encontrado")
    total = question_bank.exam_question_count(db, exam.id)
    return templates.TemplateResponse(
        request=request,
        name="exams/detail.html",
        context={
            "exam": exam,
            "total": total,
            "stats": stats.stats_for_period(db, exam_id=exam.id),
            "tags": question_bank.exam_tag_options(db, exam.id),
        },
    )
