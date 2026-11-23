from datetime import timedelta
from html import unescape

from sqlalchemy import func, select

from app.models import Attempt, Question, QuizSession, SessionItem, Topic
from app.services import practice, question_bank
from app.utils import utc_now

HX = {"HX-Request": "true"}


def start_sequential(env, feedback_mode="immediate", limit_minutes=""):
    response = env.client.post(
        "/temas/portugues/sessoes",
        data={
            "feedback_mode": feedback_mode,
            "limit_minutes": limit_minutes,
            "restart": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = response.headers["location"].split("?")[0]
    return int(location.rsplit("/", 1)[1])


def get_question(env, session_id):
    response = env.client.get(
        f"/sessoes/{session_id}/questoes/1", follow_redirects=True
    )
    assert response.status_code == 200
    return response


def test_sequential_immediate_feedback(env):
    session_id = start_sequential(env)
    response = get_question(env, session_id)

    with env.sessions() as db:
        session = db.get(QuizSession, session_id)
        item = db.scalar(
            select(SessionItem).where(
                SessionItem.session_id == session_id,
                SessionItem.position == 1,
            )
        )
        question = item.question
        correct = next(
            alternative
            for alternative in question.alternatives
            if alternative.is_correct
        )
        assert item.shown_at is not None

    assert question.statement in response.text
    assert question.general_explanation not in response.text
    assert "alt-correct" not in response.text
    assert "Resolução" not in response.text

    response = env.client.post(
        f"/sessoes/{session_id}/questoes/1/resposta",
        data={"alternative_id": str(correct.id), "timed_out": "0"},
        headers=HX,
    )
    assert response.status_code == 200
    assert "Resposta correta" in response.text
    assert question.general_explanation in unescape(response.text)
    assert "alt-correct" in response.text
    assert "Próxima questão" in response.text

    with env.sessions() as db:
        attempt = db.scalar(
            select(Attempt).where(Attempt.session_id == session_id)
        )
        assert attempt.is_correct is True
        assert attempt.selected_alternative_id == correct.id
        assert attempt.timed_out is False
        assert attempt.time_spent_seconds >= 0
        assert session.feedback_mode.value == "immediate"


def test_duplicate_answer_is_idempotent(env):
    session_id = start_sequential(env)
    get_question(env, session_id)
    with env.sessions() as db:
        item = db.scalar(
            select(SessionItem).where(SessionItem.session_id == session_id)
        )
        correct = next(
            alternative
            for alternative in item.question.alternatives
            if alternative.is_correct
        )
        correct_id = correct.id

    for _ in range(2):
        response = env.client.post(
            f"/sessoes/{session_id}/questoes/1/resposta",
            data={"alternative_id": str(correct_id), "timed_out": "0"},
            headers=HX,
        )
        assert response.status_code == 200

    with env.sessions() as db:
        count = db.scalar(
            select(func.count(Attempt.id)).where(
                Attempt.session_id == session_id
            )
        )
        assert count == 1


def test_end_mode_hides_feedback_until_result(env):
    session_id = start_sequential(env, feedback_mode="end")
    get_question(env, session_id)

    with env.sessions() as db:
        item = db.scalar(
            select(SessionItem).where(SessionItem.session_id == session_id)
        )
        question = item.question
        wrong = next(
            alternative
            for alternative in question.alternatives
            if not alternative.is_correct
        )

    response = env.client.post(
        f"/sessoes/{session_id}/questoes/1/resposta",
        data={"alternative_id": str(wrong.id), "timed_out": "0"},
        headers=HX,
    )
    assert response.status_code == 200
    assert "Resposta registrada" in response.text
    assert "alt-correct" not in response.text
    assert question.general_explanation not in response.text

    response = env.client.post(
        f"/sessoes/{session_id}/encerrar", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Revisão das questões" in response.text
    assert "Sua resposta — incorreta" in response.text
    assert question.general_explanation in unescape(response.text)
    assert "alt-correct" in response.text


def test_answer_required_and_timeout(env):
    session_id = start_sequential(env)
    response = get_question(env, session_id)
    assert response.status_code == 200

    response = env.client.post(
        f"/sessoes/{session_id}/questoes/1/resposta",
        data={"alternative_id": "", "timed_out": "0"},
        headers=HX,
    )
    assert "Selecione uma alternativa." in response.text
    with env.sessions() as db:
        assert (
            db.scalar(
                select(func.count(Attempt.id)).where(
                    Attempt.session_id == session_id
                )
            )
            == 0
        )

    with env.sessions() as db:
        item = db.scalar(
            select(SessionItem).where(
                SessionItem.session_id == session_id,
                SessionItem.position == 1,
            )
        )
        item.shown_at = utc_now() - timedelta(minutes=5)
        session = db.get(QuizSession, session_id)
        session.per_question_limit_seconds = 60
        db.commit()

    response = env.client.get(f"/sessoes/{session_id}/questoes/1")
    assert response.status_code == 200
    assert "Tempo esgotado" in response.text

    with env.sessions() as db:
        attempt = db.scalar(
            select(Attempt).where(Attempt.session_id == session_id)
        )
        assert attempt.timed_out is True
        assert attempt.selected_alternative_id is None
        assert attempt.is_correct is False
        assert attempt.time_spent_seconds >= 60


def test_random_session_has_ten_unique_questions(env):
    response = env.client.post(
        "/simulados/aleatorios",
        data={
            "count": "10",
            "topic_slug": "",
            "exam_id": "",
            "feedback_mode": "immediate",
            "limit_minutes": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    session_id = int(response.headers["location"].split("?")[0].rsplit("/", 1)[1])

    with env.sessions() as db:
        session = db.get(QuizSession, session_id)
        assert session.total_planned == 10
        question_ids = [item.question_id for item in session.items]
        assert len(question_ids) == 10
        assert len(set(question_ids)) == 10
        assert all(
            question.review_status.value == "approved"
            for question in db.scalars(
                select(Question).where(Question.id.in_(question_ids))
            ).all()
        )


def test_sequential_session_resumes(env):
    session_id = start_sequential(env)
    response = env.client.post(
        "/temas/portugues/sessoes",
        data={
            "feedback_mode": "end",
            "limit_minutes": "",
            "restart": "0",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/sessoes/{session_id}")

    with env.sessions() as db:
        sessions = list(
            db.scalars(
                select(QuizSession).where(QuizSession.topic_id.is_not(None))
            ).all()
        )
        assert len(sessions) == 1


def test_parent_topic_practice_includes_descendants(env):
    with env.sessions() as db:
        parent = db.scalar(select(Topic).where(Topic.slug == "economia"))
        descendants = question_bank.descendant_topic_ids(db, parent.slug)
        expected = practice.get_question_count(db, topic_ids=descendants)
    assert expected > 0

    response = env.client.post(
        "/temas/economia/sessoes",
        data={
            "feedback_mode": "immediate",
            "limit_minutes": "",
            "restart": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    session_id = int(response.headers["location"].split("?")[0].rsplit("/", 1)[1])
    with env.sessions() as db:
        session = db.get(QuizSession, session_id)
        assert session.total_planned == expected
