from sqlalchemy import select

from app.models import Question, SessionItem, Topic
from app.services import practice, question_bank
from app.services.question_bank import performance_for_questions

HX = {"HX-Request": "true"}


def test_question_bank_filters(env):
    response = env.client.get(
        "/questoes?concurso=bacen-2024-analista-economia-financas"
        "&banca=CEBRASPE&ano=2024&tipo=true_false"
    )
    assert response.status_code == 200
    assert "BACEN" in response.text

    response = env.client.get("/questoes?q=q050")
    assert response.status_code == 200
    assert "bacen-2024-analista-economia-financas-q050" in response.text

    response = env.client.get("/questoes?tema=economia&q=q051")
    assert response.status_code == 200
    assert "bacen-2024-analista-economia-financas-q051" in response.text

    response = env.client.get("/questoes?tag=macro-contas-nacionais&q=q041")
    assert response.status_code == 200
    assert "bacen-2024-analista-economia-financas-q041" in response.text

    response = env.client.get("/questoes?q=crase")
    assert response.status_code == 200
    assert "pt-001" in response.text

    response = env.client.get("/questoes?situacao=unseen")
    assert response.status_code == 200
    assert "Questões" in response.text


def test_question_detail_shows_source_and_generated_explanation(env):
    with env.sessions() as db:
        question = db.scalar(
            select(Question).where(
                Question.external_id
                == "bacen-2024-analista-economia-financas-q050"
            )
        )
        question_id = question.id

    response = env.client.get(f"/questoes/{question_id}")
    assert response.status_code == 200
    assert "Banca: CEBRASPE" in response.text
    assert "Explicação gerada" in response.text
    assert "/media/bacen-2024/bacen-2024-q050-ppf.png" in response.text
    assert "Ver gabarito comentado" in response.text


def test_question_performance_last_five(env):
    with env.sessions() as db:
        question = db.scalar(
            select(Question).where(Question.external_id == "pt-001")
        )
        correct = next(
            alternative
            for alternative in question.alternatives
            if alternative.is_correct
        )
        wrong = next(
            alternative
            for alternative in question.alternatives
            if not alternative.is_correct
        )
        for alternative, expected in (
            (wrong, False),
            (correct, True),
            (wrong, False),
        ):
            session = practice.start_retry_session(db, question)
            item = db.scalar(
                select(SessionItem).where(SessionItem.session_id == session.id)
            )
            practice.record_answer(db, session, item, alternative.id)
        performance = performance_for_questions(db, [question.id])[question.id]

    assert performance.total == 3
    assert performance.correct == 1
    assert len(performance.dots) == 5
    assert performance.dots[0] is None
    assert performance.dots[1] is None
    assert performance.dots[2].is_correct is False
    assert performance.dots[3].is_correct is True
    assert performance.dots[4].is_correct is False


def test_retry_marks_recent_error_resolved(env):
    response = env.client.post(
        "/temas/portugues/sessoes",
        data={
            "feedback_mode": "immediate",
            "limit_minutes": "",
            "restart": "1",
        },
        follow_redirects=False,
    )
    session_id = int(response.headers["location"].split("?")[0].rsplit("/", 1)[1])
    env.client.get(f"/sessoes/{session_id}/questoes/1", follow_redirects=True)
    with env.sessions() as db:
        item = db.scalar(
            select(SessionItem).where(
                SessionItem.session_id == session_id,
                SessionItem.position == 1,
            )
        )
        question_id = item.question_id
        wrong = next(
            alternative
            for alternative in item.question.alternatives
            if not alternative.is_correct
        )
    env.client.post(
        f"/sessoes/{session_id}/questoes/1/resposta",
        data={"alternative_id": str(wrong.id), "timed_out": "0"},
        headers=HX,
    )
    env.client.post(f"/sessoes/{session_id}/encerrar")

    response = env.client.get(f"/sessoes/{session_id}/resultado")
    assert response.status_code == 200
    assert "Desempenho por tema nesta sessão" in response.text
    assert "Tentar novamente" in response.text

    response = env.client.post(
        f"/questoes/{question_id}/refazer", follow_redirects=False
    )
    retry_id = int(response.headers["location"].split("?")[0].rsplit("/", 1)[1])
    env.client.get(f"/sessoes/{retry_id}/questoes/1", follow_redirects=True)
    with env.sessions() as db:
        item = db.scalar(
            select(SessionItem).where(SessionItem.session_id == retry_id)
        )
        correct = next(
            alternative
            for alternative in item.question.alternatives
            if alternative.is_correct
        )
    env.client.post(
        f"/sessoes/{retry_id}/questoes/1/resposta",
        data={"alternative_id": str(correct.id), "timed_out": "0"},
        headers=HX,
    )

    response = env.client.get("/estatisticas")
    assert response.status_code == 200
    assert "Refeita e acertada" in response.text

    response = env.client.get("/estatisticas?resolvidos=0")
    assert response.status_code == 200
    assert "Refeita e acertada" not in response.text


def test_topic_hierarchy(env):
    with env.sessions() as db:
        child = db.scalar(select(Topic).where(Topic.slug == "politica-monetaria"))
        parent = db.scalar(select(Topic).where(Topic.slug == "macroeconomia"))
        assert child.parent_id == parent.id
        assert question_bank.descendant_topic_ids(db, "economia")


def test_api_question_includes_context_and_provenance(env):
    response = env.client.get(
        "/api/questions/bacen-2024-analista-economia-financas-q050"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["context"]
    assert data["media_url"].endswith("q050-ppf.png")
    assert data["origin"] == "official"
    assert data["answer_source"] == "official_key"
    assert data["explanation_source"] == "generated"
    assert data["exam_details"]["organization"] == "CEBRASPE"
    assert data["tag"]["slug"] == "micro-teoria"
    assert data["tag"]["area"] == "Microeconomia"


def test_dots_are_colored_on_list_and_detail(env):
    with env.sessions() as db:
        question = db.scalar(
            select(Question).where(Question.external_id == "pt-001")
        )
        correct = next(
            alternative
            for alternative in question.alternatives
            if alternative.is_correct
        )
        wrong = next(
            alternative
            for alternative in question.alternatives
            if not alternative.is_correct
        )
        question_id = question.id
        for alternative in (correct, wrong):
            session = practice.start_retry_session(db, question)
            item = db.scalar(
                select(SessionItem).where(SessionItem.session_id == session.id)
            )
            practice.record_answer(db, session, item, alternative.id)

    response = env.client.get("/questoes?q=pt-001")
    assert response.status_code == 200
    assert "perf-dot is-correct" in response.text
    assert "perf-dot is-wrong" in response.text

    response = env.client.get(f"/questoes/{question_id}")
    assert response.status_code == 200
    assert "perf-dot is-correct" in response.text
    assert "perf-dot is-wrong" in response.text


def test_material_related_dots_are_colored(env):
    with env.sessions() as db:
        question = db.scalar(
            select(Question).where(
                Question.external_id == "bacen-2024-analista-economia-financas-q041"
            )
        )
        correct = next(
            alternative
            for alternative in question.alternatives
            if alternative.is_correct
        )
        session = practice.start_retry_session(db, question)
        item = db.scalar(
            select(SessionItem).where(SessionItem.session_id == session.id)
        )
        practice.record_answer(db, session, item, correct.id)

    response = env.client.get("/materiais/macro-contas-nacionais-modelos")
    assert response.status_code == 200
    assert "perf-dot is-correct" in response.text


def test_material_suggestions_only_after_session(env):
    with env.sessions() as db:
        question = db.scalar(
            select(Question).where(
                Question.external_id == "bacen-2024-analista-economia-financas-q006"
            )
        )
        correct = next(
            alternative
            for alternative in question.alternatives
            if alternative.is_correct
        )
        question_id = question.id

    response = env.client.post(
        f"/questoes/{question_id}/refazer", follow_redirects=False
    )
    session_id = int(response.headers["location"].split("?")[0].rsplit("/", 1)[1])
    env.client.get(f"/sessoes/{session_id}/questoes/1", follow_redirects=True)
    response = env.client.post(
        f"/sessoes/{session_id}/questoes/1/resposta",
        data={"alternative_id": str(correct.id), "timed_out": "0"},
        headers=HX,
    )
    assert response.status_code == 200
    assert "/materiais/" not in response.text
    assert "Entenda o tema" not in response.text

    response = env.client.get(f"/sessoes/{session_id}/resultado")
    assert response.status_code == 200
    assert "Materiais para reforçar" in response.text
    assert "Interpretação de textos, coesão e orações adjetivas" in response.text
    assert "Crase, concordância e pontuação" not in response.text


def test_material_relevance_and_coverage(env):
    with env.sessions() as db:
        q006 = db.scalar(
            select(Question).where(
                Question.external_id == "bacen-2024-analista-economia-financas-q006"
            )
        )
        q006_slugs = [material.slug for material in question_bank.related_materials(db, q006)]
        assert "portugues-interpretacao-coesao" in q006_slugs
        assert "portugues-gramatica-crase-concordancia" not in q006_slugs

        questions = list(db.scalars(select(Question)).all())
        assert len(questions) == 192
        for question in questions:
            assert question_bank.related_materials(db, question), question.external_id


def test_tag_area_stats(env):
    with env.sessions() as db:
        question = db.scalar(
            select(Question).where(
                Question.external_id == "bacen-2024-analista-economia-financas-q041"
            )
        )
        correct = next(
            alternative
            for alternative in question.alternatives
            if alternative.is_correct
        )
        session = practice.start_retry_session(db, question)
        item = db.scalar(
            select(SessionItem).where(SessionItem.session_id == session.id)
        )
        practice.record_answer(db, session, item, correct.id)

    response = env.client.get("/estatisticas")
    assert response.status_code == 200
    assert "Desempenho por área" in response.text
    assert "Desempenho por assunto" in response.text
    assert "Contas Nacionais" in response.text
    assert "Economia" in response.text


def test_bacen_agency_and_exam_filters_use_shared_links(env):
    response = env.client.get("/questoes?orgao=BACEN&q=q051")
    assert response.status_code == 200
    assert "bacen-2024-analista-tecnologia-informacao-q051" in response.text

    response = env.client.get(
        "/questoes?concurso=bacen-2024-analista-tecnologia-informacao&q=q001"
    )
    assert response.status_code == 200
    assert "bacen-2024-analista-economia-financas-q001" in response.text
