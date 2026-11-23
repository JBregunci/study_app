from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import practice, stats, topic_tree
from ..templating import templates
from ..utils import local_today

router = APIRouter()


@router.get("/", name="dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    series = stats.daily_series(db, 14)
    chart_max = max((day.total for day in series), default=0) or 1
    in_progress = [
        (session, practice.session_progress(db, session))
        for session in practice.in_progress_sessions(db)
    ]
    all_topics = topic_tree.load_topics(db)
    children = topic_tree.children_map(all_topics)
    topics = topic_tree.top_level(all_topics)
    direct_stats = {item.topic.id: item.stats for item in stats.topic_stats(db)}
    aggregated_stats = [
        stats.TopicStats(
            topic=topic,
            stats=topic_tree.subtree_stats(children, direct_stats, topic.id),
        )
        for topic in topics
    ]
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "today": local_today(),
            "today_stats": stats.stats_for_day(db),
            "overall": stats.stats_for_period(db),
            "streak": stats.streak(db),
            "series": series,
            "chart_max": chart_max,
            "topic_stats": aggregated_stats,
            "recent_sessions": stats.session_summaries(db, 6),
            "in_progress": in_progress,
            "topics": topics,
        },
    )
