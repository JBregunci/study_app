from sqlalchemy import select

from app.models import Alternative, Question
from app.config import CATALOG_DIR, MATERIALS_DIR, QUESTIONS_DIR
from app.services.audit import audit_database, audit_sources


def test_audit_clean_library(env):
    with env.sessions() as db:
        report = audit_database(db)
        assert report.ok, report.critical
    source_report = audit_sources(QUESTIONS_DIR, CATALOG_DIR, MATERIALS_DIR)
    assert source_report.ok, source_report.critical


def test_audit_detects_normalized_duplicate(env):
    with env.sessions() as db:
        original = db.scalar(
            select(Question).where(Question.external_id == "pt-001")
        )
        duplicate = Question(
            external_id="dup-normalizada",
            topic_id=original.topic_id,
            exam_id=original.exam_id,
            tag_id=original.tag_id,
            type=original.type,
            statement=original.statement.replace(".", "!"),
            context=original.context,
            media_url=original.media_url,
            context_media_url=original.context_media_url,
            difficulty=original.difficulty,
            source=original.source,
            source_url=original.source_url,
            source_question_number=original.source_question_number,
            general_explanation=original.general_explanation,
            origin=original.origin,
            answer_source=original.answer_source,
            explanation_source=original.explanation_source,
            review_status=original.review_status,
            content_hash="f" * 64,
        )
        db.add(duplicate)
        db.flush()
        for alternative in original.alternatives:
            db.add(
                Alternative(
                    question_id=duplicate.id,
                    label=alternative.label,
                    text=alternative.text,
                    is_correct=alternative.is_correct,
                    explanation=alternative.explanation,
                    position=alternative.position,
                    is_active=alternative.is_active,
                )
            )
        db.commit()
        report = audit_database(db)
    assert not report.ok
    assert any("normalizadas duplicadas" in message for message in report.critical)
