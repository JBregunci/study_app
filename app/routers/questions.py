from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ReviewStatus
from ..services import practice, question_bank
from ..templating import templates
from ..web import redirect

router = APIRouter()

QUESTION_TYPE_VALUES = {"single_choice", "true_false"}
DIFFICULTY_VALUES = {"facil", "medio", "dificil"}
SITUATION_VALUES = {"", "unseen", "error"}
ORDER_VALUES = {"recent", "errors", "unseen"}


@router.get("/questoes", name="questions_list")
def questions_list(
    request: Request,
    db: Session = Depends(get_db),
    pagina: int = 1,
    q: str = "",
    tema: str = "",
    concurso: str = "",
    orgao: str = "",
    edicao: str = "",
    banca: str = "",
    ano: str = "",
    cargo: str = "",
    tipo: str = "",
    dificuldade: str = "",
    tag: str = "",
    area: str = "",
    situacao: str = "",
    ordem: str = "recent",
):
    tipo = tipo if tipo in QUESTION_TYPE_VALUES else ""
    dificuldade = dificuldade if dificuldade in DIFFICULTY_VALUES else ""
    situacao = situacao if situacao in SITUATION_VALUES else ""
    ordem = ordem if ordem in ORDER_VALUES else "recent"
    ano_value = int(ano) if ano.isdigit() else ""

    filters = {
        "q": q,
        "topic": tema,
        "exam": concurso,
        "agency": orgao,
        "contest": edicao,
        "organization": banca,
        "year": ano_value,
        "role": cargo,
        "question_type": tipo,
        "difficulty": dificuldade,
        "tag": tag,
        "area": area,
        "situation": situacao,
        "order": ordem,
    }
    result = question_bank.list_questions(db, page=pagina, per_page=25, **filters)
    options = question_bank.filter_options(db)
    selected = {
        "q": q,
        "tema": tema,
        "concurso": concurso,
        "orgao": orgao,
        "edicao": edicao,
        "banca": banca,
        "ano": str(ano_value) if ano_value != "" else "",
        "cargo": cargo,
        "tipo": tipo,
        "dificuldade": dificuldade,
        "tag": tag,
        "area": area,
        "situacao": situacao,
        "ordem": ordem,
    }
    base_params = {key: value for key, value in selected.items() if value}
    base_params.pop("ordem", None)
    if ordem != "recent":
        base_params["ordem"] = ordem
    base_qs = urlencode(base_params)
    return templates.TemplateResponse(
        request=request,
        name="questions/list.html",
        context={
            "result": result,
            "options": options,
            "selected": selected,
            "base_qs": base_qs,
        },
    )


@router.get("/questoes/{question_id}", name="question_detail")
def question_detail(
    question_id: int, request: Request, db: Session = Depends(get_db)
):
    question = question_bank.get_question(db, question_id)
    if question is None or question.review_status != ReviewStatus.approved:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    performance = question_bank.performance_for_questions(db, [question.id])[question.id]
    attempts = question_bank.question_attempts(db, question.id)
    materials = question_bank.related_materials(db, question)
    return templates.TemplateResponse(
        request=request,
        name="questions/detail.html",
        context={
            "question": question,
            "performance": performance,
            "attempts": attempts,
            "materials": materials,
            "breadcrumb": question_bank.topic_breadcrumb(question.topic),
            "alternatives": practice.display_alternatives(question),
        },
    )


@router.post("/questoes/{question_id}/refazer", name="question_retry")
def question_retry(question_id: int, db: Session = Depends(get_db)):
    question = question_bank.get_question(db, question_id)
    if question is None or question.review_status != ReviewStatus.approved:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    try:
        session = practice.start_retry_session(db, question)
    except ValueError as exc:
        return redirect(f"/questoes/{question_id}", erro=str(exc))
    return redirect(f"/sessoes/{session.id}")
