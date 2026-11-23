from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..markdown_utils import render_markdown
from ..models import Material, ReviewStatus, Tag, Topic
from ..services import question_bank
from ..templating import templates

router = APIRouter()


@router.get("/materiais", name="materials_list")
def materials_list(
    request: Request,
    db: Session = Depends(get_db),
    q: str = "",
    tema: str = "",
    tag: str = "",
):
    stmt = (
        select(Material)
        .where(Material.review_status == ReviewStatus.approved)
        .options(
            selectinload(Material.topics),
            selectinload(Material.tags),
        )
        .order_by(Material.updated_at.desc(), Material.title)
    )
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Material.title.ilike(like),
                Material.summary.ilike(like),
                Material.body_md.ilike(like),
                Material.tags.any(Tag.name.ilike(like)),
            )
        )
    if tema:
        topic_ids = question_bank.descendant_topic_ids(db, tema)
        stmt = stmt.where(Material.topics.any(Topic.id.in_(topic_ids or {-1})))
    if tag:
        stmt = stmt.where(Material.tags.any(Tag.slug == tag))
    materials = list(db.scalars(stmt).unique().all())
    options = question_bank.filter_options(db)
    selected = {"q": q, "tema": tema, "tag": tag}
    return templates.TemplateResponse(
        request=request,
        name="materials/list.html",
        context={
            "materials": materials,
            "options": options,
            "selected": selected,
            "base_qs": urlencode({k: v for k, v in selected.items() if v}),
        },
    )


@router.get("/materiais/{slug}", name="material_detail")
def material_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    material = db.scalar(
        select(Material)
        .options(
            selectinload(Material.topics),
            selectinload(Material.tags),
        )
        .where(Material.slug == slug)
    )
    if material is None or material.review_status != ReviewStatus.approved:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    related = question_bank.related_questions_for_material(db, material)
    topics = sorted(material.topics, key=lambda topic: (topic.position, topic.name))
    return templates.TemplateResponse(
        request=request,
        name="materials/detail.html",
        context={
            "material": material,
            "material_html": render_markdown(material.body_md),
            "related": related,
            "primary_topic": topics[0] if topics else None,
            "breadcrumb": question_bank.topic_breadcrumb(topics[0] if topics else None),
        },
    )
