from html import unescape

from pydantic import ValidationError
from sqlalchemy import func, select

from app.models import (
    Alternative,
    Question,
    QuestionType,
    ReviewStatus,
)
from app.schemas import QuestionFile
from app.services.question_import import import_all, import_payload


def question_payload(
    external_id="teste-001",
    topic="tema-teste",
    statement="Qual é a resposta correta?",
    explanations=True,
    **overrides,
):
    data = {
        "external_id": external_id,
        "topic": topic,
        "tag": "logica",
        "type": "single_choice",
        "statement": statement,
        "general_explanation": "Explicação geral da questão.",
        "review_status": "approved",
        "alternatives": [
            {
                "label": "A",
                "text": "Alternativa correta",
                "is_correct": True,
                "explanation": "Porque A está correta.",
            },
            {
                "label": "B",
                "text": "Alternativa incorreta",
                "is_correct": False,
                "explanation": "Porque B está incorreta.",
            },
        ],
    }
    if not explanations:
        data["alternatives"][1]["explanation"] = ""
    data.update(overrides)
    return {
        "topics": [{"slug": topic, "name": "Tema teste"}],
        "exams": [],
        "questions": [data],
    }


def test_sample_bank_imports(env):
    with env.sessions() as db:
        questions = list(
            db.scalars(select(Question).order_by(Question.external_id)).all()
        )
        assert len(questions) >= 25
        bacen = [
            question
            for question in questions
            if question.external_id.startswith("bacen-2024-analista-economia-financas-")
        ]
        assert len(bacen) == 115
        assert len({question.content_hash for question in questions}) == len(questions)
        assert all(
            question.review_status == ReviewStatus.approved
            for question in questions
        )
        assert {"portugues-gramatica", "direito-constitucional", "raciocinio-logico", "informatica"} <= {
            question.topic.slug for question in questions
        }

        for question in questions:
            active = [alt for alt in question.alternatives if alt.is_active]
            assert len(active) >= 2
            assert sum(1 for alt in active if alt.is_correct) == 1
            if question.type == QuestionType.single_choice:
                assert all(alt.explanation.strip() for alt in active)
            else:
                assert {alt.label for alt in active} == {"C", "E"}
            assert question.tag is not None


def test_sample_bank_import_is_idempotent(env):
    from app.config import CATALOG_DIR, QUESTIONS_DIR

    with env.sessions() as db:
        before = db.scalar(select(Question.id).order_by(Question.id))
        report = import_all(db, QUESTIONS_DIR, CATALOG_DIR, ReviewStatus.approved)
        assert report.created == 0
        assert report.updated == len(
            list(db.scalars(select(Question)).all())
        )
        assert not report.errors
        assert db.scalar(select(Question.id).order_by(Question.id)) == before


def test_invalid_question_shape_is_rejected():
    payload = question_payload()
    payload["questions"][0]["alternatives"][1]["is_correct"] = True
    try:
        QuestionFile.model_validate(payload)
    except ValidationError as exc:
        assert "exatamente uma alternativa" in str(exc)
    else:
        raise AssertionError("payload inválido foi aceito")

    payload = question_payload(type="true_false")
    try:
        QuestionFile.model_validate(payload)
    except ValidationError as exc:
        assert "C e E" in str(exc)
    else:
        raise AssertionError("certo/errado com labels inválidos foi aceito")


def test_approved_question_requires_complete_explanations(env):
    payload = QuestionFile.model_validate(question_payload(explanations=False))
    with env.sessions() as db:
        report = import_payload(
            db, payload, default_status=ReviewStatus.approved
        )
        assert report.created == 0
        assert report.skipped == 1
        assert any("alternativa B" in error for error in report.errors)
        assert (
            db.scalar(
                select(Question).where(Question.external_id == "teste-001")
            )
            is None
        )


def test_duplicate_content_is_reused(env):
    first = question_payload(external_id="dup-001")["questions"][0]
    second = dict(first)
    second["external_id"] = "dup-002"
    payload = QuestionFile.model_validate(
        {
            "topics": [{"slug": "tema-teste", "name": "Tema teste"}],
            "exams": [],
            "questions": [first, second],
        }
    )
    with env.sessions() as db:
        report = import_payload(
            db, payload, default_status=ReviewStatus.approved
        )
        assert report.created == 1
        assert report.reused == 1
        assert report.skipped == 0
        assert not report.errors
        assert (
            db.scalar(
                select(func.count(Question.id)).where(
                    Question.external_id.in_(["dup-001", "dup-002"])
                )
            )
            == 1
        )


def test_api_import_defaults_to_draft(env):
    payload = question_payload(external_id="api-001", topic="api-teste")
    payload["questions"][0].pop("review_status")
    response = env.client.post("/api/questions/import", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 1
    assert not data["errors"]

    with env.sessions() as db:
        question = db.scalar(
            select(Question).where(Question.external_id == "api-001")
        )
        assert question is not None
        assert question.review_status == ReviewStatus.draft
        assert len(question.alternatives) == 2
        assert all(
            isinstance(alternative, Alternative)
            for alternative in question.alternatives
        )


def test_api_question_lookup_and_404(env):
    response = env.client.get("/api/questions/pt-001")
    assert response.status_code == 200
    data = response.json()
    assert data["external_id"] == "pt-001"
    assert len(data["alternatives"]) == 5

    response = env.client.get("/api/questions/inexistente")
    assert response.status_code == 404
    assert response.json()["detail"]

    response = env.client.get("/pagina-inexistente")
    assert response.status_code == 404
    assert "Página não encontrada" in response.text


def test_bacen_all_answers_match_official_key(env):
    basics_rows = [
        'C E C E E C E C E E C C E C E E E C C C',
        'E E E E C E C E C E E C C E C E E C C C',
        'C E E X E C E C C E',
    ]
    specific_rows = [
        'E X C E C C C C E C C C E X E C E C C E',
        'C C C C E E E C E C E E X E E C C E C C',
        'E C E C E C C E E C C E C E C C C E C E',
        'E C C E E C C E X E',
    ]
    answers = {}
    number = 1
    for row in basics_rows:
        for value in row.split():
            answers[number] = value
            number += 1
    number = 51
    for row in specific_rows:
        for value in row.split():
            answers[number] = value
            number += 1

    with env.sessions() as db:
        for number, answer in answers.items():
            if answer == 'X':
                continue
            question = db.scalar(
                select(Question).where(
                    Question.external_id
                    == f'bacen-2024-analista-economia-financas-q{number:03d}'
                )
            )
            assert question is not None, number
            correct = next(
                alternative
                for alternative in question.alternatives
                if alternative.is_active and alternative.is_correct
            )
            assert correct.label == answer, number
            assert question.answer_source.value == 'official_key'
            assert question.explanation_source.value == 'generated'
            assert question.general_explanation
            assert question.source_question_number == str(number)


def test_bacen_annulled_items_are_absent(env):
    with env.sessions() as db:
        for number in (44, 52, 64, 83, 119):
            question = db.scalar(
                select(Question).where(
                    Question.external_id
                    == f'bacen-2024-analista-economia-financas-q{number:03d}'
                )
            )
            assert question is None, number


def test_bacen_contexts_and_media(env):
    with env.sessions() as db:
        q47 = db.scalar(
            select(Question).where(
                Question.external_id == 'bacen-2024-analista-economia-financas-q047'
            )
        )
        q71 = db.scalar(
            select(Question).where(
                Question.external_id == 'bacen-2024-analista-economia-financas-q071'
            )
        )
        assert q47.media_url.endswith('q047-oferta-demanda.png')
        assert q71.context_media_url.endswith('q071-072-jogo.png')
        assert q47.context
        assert q71.context


def test_bacen_ti_answers_and_shared_basics(env):
    rows = [
        'E C X E X X C E C E X C C E E C E C C E',
        'E E C E C C E C E C E C E C C C E C E C',
        'E E E E C E C E C C X C E C C E C E E C',
        'C E C C E E E C C C',
    ]
    answers = {}
    number = 51
    for row in rows:
        for value in row.split():
            answers[number] = value
            number += 1

    with env.sessions() as db:
        for number, answer in answers.items():
            if answer == 'X':
                continue
            question = db.scalar(
                select(Question).where(
                    Question.external_id
                    == f'bacen-2024-analista-tecnologia-informacao-q{number:03d}'
                )
            )
            assert question is not None, number
            correct = next(
                alternative
                for alternative in question.alternatives
                if alternative.is_active and alternative.is_correct
            )
            assert correct.label == answer, number

        for annulled in (53, 55, 56, 61, 101):
            assert (
                db.scalar(
                    select(Question).where(
                        Question.external_id
                        == f'bacen-2024-analista-tecnologia-informacao-q{annulled:03d}'
                    )
                )
                is None
            )

        basic = db.scalar(
            select(Question).where(
                Question.external_id == 'bacen-2024-analista-economia-financas-q001'
            )
        )
        exam_slugs = {exam.slug for exam in basic.exams}
        assert 'bacen-2024-analista-economia-financas' in exam_slugs
        assert 'bacen-2024-analista-tecnologia-informacao' in exam_slugs

        from app.models import Exam
        from app.services import question_bank

        ti_exam = db.scalar(
            select(Exam).where(
                Exam.slug == 'bacen-2024-analista-tecnologia-informacao'
            )
        )
        assert question_bank.exam_question_count(db, ti_exam.id) == 114
