from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import stats
from ..templating import templates
from ..utils import local_today

router = APIRouter()

PERIODS = {
    7: "Últimos 7 dias",
    30: "Últimos 30 dias",
    90: "Últimos 90 dias",
    0: "Todo o período",
}


@router.get("/estatisticas", name="stats_page")
def stats_page(
    request: Request,
    dias: int = 30,
    resolvidos: int = 1,
    db: Session = Depends(get_db),
):
    if dias not in PERIODS:
        dias = 30
    today = local_today()
    start = today - timedelta(days=dias - 1) if dias else None
    chart_days = dias or 30
    series = stats.daily_series(db, chart_days)
    chart_max = max((day.total for day in series), default=0) or 1
    return templates.TemplateResponse(
        request=request,
        name="stats/index.html",
        context={
            "periods": PERIODS,
            "selected_period": dias,
            "period_label": PERIODS[dias],
            "overview": stats.stats_for_period(db, start=start, end=today),
            "series": series,
            "chart_max": chart_max,
            "chart_days": chart_days,
            "topic_stats": stats.topic_stats(db, start=start, end=today),
            "tag_stats": stats.tag_stats(db, start=start, end=today),
            "area_stats": stats.area_stats(db, start=start, end=today),
            "wrong_attempts": stats.recent_wrong_attempts(
                db,
                limit=15,
                start=start,
                include_resolved=bool(resolvidos),
            ),
            "show_resolved": bool(resolvidos),
            "recent_sessions": stats.session_summaries(db, 10),
            "streak": stats.streak(db),
            "today": today,
        },
    )
