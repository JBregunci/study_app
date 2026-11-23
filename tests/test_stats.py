from datetime import timedelta

from sqlalchemy import select

from app.models import Attempt, FeedbackMode, SessionItem
from app.services import practice, stats
from app.utils import local_today


def seed_attempts(env):
    yesterday = local_today() - timedelta(days=1)
    with env.sessions() as db:
        session = practice.start_random_session(
            db, 10, FeedbackMode.immediate, None
        )
        items = list(
            db.scalars(
                select(SessionItem)
                .where(SessionItem.session_id == session.id)
                .order_by(SessionItem.position)
            ).all()
        )
        first = items[0]
        second = items[1]
        correct = next(
            alternative
            for alternative in first.question.alternatives
            if alternative.is_correct
        )
        wrong = next(
            alternative
            for alternative in second.question.alternatives
            if not alternative.is_correct
        )
        practice.record_answer(db, session, first, correct.id)
        practice.record_answer(db, session, second, wrong.id)
        first_attempt = db.scalar(
            select(Attempt).where(Attempt.session_id == session.id, Attempt.question_id == first.question_id)
        )
        first_attempt.answered_on = yesterday
        db.commit()
        return session.id


def test_daily_stats_streak_and_topic_breakdown(env):
    seed_attempts(env)
    with env.sessions() as db:
        today = stats.stats_for_day(db)
        assert today.total == 1
        assert today.correct == 0
        assert today.incorrect == 1
        assert today.blank == 0

        overall = stats.stats_for_period(db)
        assert overall.total == 2
        assert overall.correct == 1
        assert overall.incorrect == 1
        assert stats.streak(db) == 2

        series = stats.daily_series(db, 2)
        assert [day.total for day in series] == [1, 1]

        topics = stats.topic_stats(db)
        assert sum(item.stats.total for item in topics) == 2

        wrong = stats.recent_wrong_attempts(db)
        assert len(wrong) == 1
        assert wrong[0].attempt.is_correct is False
        assert wrong[0].selected is not None
        assert wrong[0].correct is not None


def test_stats_page_and_dashboard_render(env):
    seed_attempts(env)
    response = env.client.get("/estatisticas")
    assert response.status_code == 200
    assert "Estatísticas" in response.text
    assert "Erros recentes" in response.text

    response = env.client.get("/")
    assert response.status_code == 200
    assert "Seu painel de estudos" in response.text
    assert "Sequência" in response.text
