from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import FeedbackMode, Topic
from ..services import practice, question_bank, stats, topic_tree
from ..templating import templates
from ..web import parse_feedback_mode, parse_limit_seconds, redirect

router = APIRouter()


def _get_topic(db: Session, slug: str) -> Topic:
    topic = db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404, detail="Tema não encontrado")
    return topic


@router.get("/temas", name="topics_list")
def list_topics(request: Request, db: Session = Depends(get_db)):
    all_topics = topic_tree.load_topics(db)
    children = topic_tree.children_map(all_topics)
    topics = topic_tree.top_level(all_topics)
    direct_counts = stats.approved_counts_by_topic(db)
    direct_stats = {item.topic.id: item.stats for item in stats.topic_stats(db)}
    return templates.TemplateResponse(
        request=request,
        name="topics/list.html",
        context={
            "topics": topics,
            "counts": {
                topic.id: topic_tree.subtree_count(children, direct_counts, topic.id)
                for topic in topics
            },
            "stats_by_topic": {
                topic.id: topic_tree.subtree_stats(children, direct_stats, topic.id)
                for topic in topics
            },
            "in_progress": {
                topic.id: practice.get_in_progress_sequential(db, topic.id)
                for topic in topics
            },
        },
    )


@router.get("/temas/{slug}", name="topic_detail")
def topic_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    topic = _get_topic(db, slug)
    all_topics = topic_tree.load_topics(db)
    children = topic_tree.children_map(all_topics)
    direct_counts = stats.approved_counts_by_topic(db)
    direct_stats = {item.topic.id: item.stats for item in stats.topic_stats(db)}
    descendant_ids = topic_tree.subtree_ids(children, topic.id)
    child_rows = topic_tree.descendant_rows(
        children, direct_counts, direct_stats, topic.id
    )
    return templates.TemplateResponse(
        request=request,
        name="topics/detail.html",
        context={
            "topic": topic,
            "question_count": practice.get_question_count(db, topic_ids=descendant_ids),
            "topic_stats": stats.stats_for_period(db, topic_ids=descendant_ids),
            "in_progress": practice.get_in_progress_sequential(db, topic.id),
            "materials": question_bank.materials_for_topics(db, descendant_ids),
            "child_rows": child_rows,
        },
    )


@router.post("/temas/{slug}/sessoes", name="topic_start")
def start_topic_session(
    slug: str,
    db: Session = Depends(get_db),
    feedback_mode: str = Form("immediate"),
    limit_minutes: str = Form(""),
    restart: str = Form("0"),
):
    topic = _get_topic(db, slug)
    all_topics = topic_tree.load_topics(db)
    children = topic_tree.children_map(all_topics)
    descendant_ids = topic_tree.subtree_ids(children, topic.id)
    mode = parse_feedback_mode(feedback_mode, FeedbackMode.immediate)
    limit = parse_limit_seconds(limit_minutes)
    try:
        session = practice.start_sequential_session(
            db,
            topic,
            feedback_mode=mode,
            limit_seconds=limit,
            restart=restart == "1",
            topic_ids=descendant_ids,
        )
    except ValueError as exc:
        return redirect(f"/temas/{slug}", erro=str(exc))
    return redirect(f"/sessoes/{session.id}")
