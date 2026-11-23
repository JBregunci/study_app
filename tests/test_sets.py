from sqlalchemy import select

from app.models import Question, QuestionSet, QuizSession, ReviewStatus


def approved_ids(env, limit=4):
    with env.sessions() as db:
        return [
            question.id
            for question in db.scalars(
                select(Question)
                .where(Question.review_status == ReviewStatus.approved)
                .order_by(Question.id)
                .limit(limit)
            ).all()
        ]


def create_set(env, ids, name="Conjunto de teste"):
    return env.client.post(
        "/conjuntos/novo",
        data={
            "name": name,
            "description": "Descrição",
            "target_title": "Analista",
            "exam_id": "",
            "default_feedback_mode": "end",
            "default_limit_minutes": "",
            "question_ids": [str(question_id) for question_id in ids],
        },
        follow_redirects=False,
    )


def test_create_set_and_practice_in_order(env):
    ids = approved_ids(env)
    response = create_set(env, ids)
    assert response.status_code == 303
    set_id = int(
        response.headers["location"].split("?")[0].rsplit("/", 1)[1]
    )

    with env.sessions() as db:
        question_set = db.get(QuestionSet, set_id)
        assert [item.question_id for item in question_set.items] == ids
        assert question_set.name == "Conjunto de teste"
        first_question = db.get(Question, ids[0])
        first_statement = first_question.statement

    response = env.client.get(f"/conjuntos/{set_id}")
    assert response.status_code == 200
    assert "Conjunto de teste" in response.text

    response = env.client.post(
        f"/conjuntos/{set_id}/sessoes",
        data={"feedback_mode": "end", "limit_minutes": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    session_id = int(
        response.headers["location"].split("?")[0].rsplit("/", 1)[1]
    )
    with env.sessions() as db:
        session = db.get(QuizSession, session_id)
        assert session.total_planned == len(ids)
        assert [item.question_id for item in session.items] == ids

    response = env.client.get(
        f"/sessoes/{session_id}/questoes/1", follow_redirects=True
    )
    assert response.status_code == 200
    assert first_statement in response.text


def test_set_update_replaces_questions(env):
    ids = approved_ids(env, 4)
    response = create_set(env, ids[:2])
    set_id = int(
        response.headers["location"].split("?")[0].rsplit("/", 1)[1]
    )
    new_ids = list(reversed(ids[2:]))
    response = env.client.post(
        f"/conjuntos/{set_id}",
        data={
            "name": "Conjunto atualizado",
            "description": "",
            "target_title": "",
            "exam_id": "",
            "default_feedback_mode": "immediate",
            "default_limit_minutes": "2",
            "question_ids": [str(question_id) for question_id in new_ids],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    with env.sessions() as db:
        question_set = db.get(QuestionSet, set_id)
        assert question_set.name == "Conjunto atualizado"
        assert [item.question_id for item in question_set.items] == new_ids
        assert question_set.default_feedback_mode.value == "immediate"
        assert question_set.default_limit_seconds == 120


def test_set_requires_at_least_one_question(env):
    response = create_set(env, [])
    assert response.status_code == 400
    assert "Selecione pelo menos uma questão." in response.text


def test_set_delete(env):
    response = create_set(env, approved_ids(env, 2))
    set_id = int(
        response.headers["location"].split("?")[0].rsplit("/", 1)[1]
    )
    response = env.client.post(
        f"/conjuntos/{set_id}/excluir", follow_redirects=False
    )
    assert response.status_code == 303
    with env.sessions() as db:
        assert db.get(QuestionSet, set_id) is None
