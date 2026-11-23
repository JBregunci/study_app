from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    Alternative,
    Exam,
    Question,
    QuestionType,
    ReviewStatus,
    Tag,
    Topic,
)
from ..schemas import (
    ExamCatalog,
    QuestionFile,
    QuestionIn,
    TagCatalog,
    TopicCatalog,
)


@dataclass
class ImportReport:
    files: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def merge(self, other: ImportReport) -> None:
        self.files += other.files
        self.created += other.created
        self.updated += other.updated
        self.skipped += other.skipped
        self.errors.extend(other.errors)

    def to_dict(self) -> dict:
        return {
            "files": self.files,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
        }


def _format_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        messages = []
        for error in exc.errors()[:5]:
            location = ".".join(str(part) for part in error["loc"])
            messages.append(f"{location}: {error['msg']}")
        return "; ".join(messages)
    return str(exc)


def content_hash(question: QuestionIn) -> str:
    payload = {
        "type": question.type.value,
        "context": question.context.strip(),
        "statement": question.statement.strip(),
        "alternatives": [
            {
                "label": alt.label,
                "text": alt.text.strip(),
                "is_correct": alt.is_correct,
            }
            for alt in sorted(question.alternatives, key=lambda item: item.label)
        ],
    }
    serialized = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def _completeness_errors(question: QuestionIn, status: ReviewStatus) -> list[str]:
    if status != ReviewStatus.approved:
        return []
    errors = []
    if not question.general_explanation.strip():
        errors.append("explicação geral obrigatória para questão aprovada")
    if question.type == QuestionType.single_choice:
        for alternative in question.alternatives:
            if not alternative.explanation.strip():
                errors.append(
                    f"explicação obrigatória para a alternativa {alternative.label} de questão aprovada"
                )
    return errors


def _topics_map(db: Session) -> dict[str, Topic]:
    return {topic.slug: topic for topic in db.scalars(select(Topic)).all()}


def _exams_map(db: Session) -> dict[str, Exam]:
    return {exam.slug: exam for exam in db.scalars(select(Exam)).all()}


def upsert_topics(
    db: Session,
    topics: dict[str, Topic],
    items,
    source_name: str,
    report: ImportReport,
) -> None:
    slugs = [item.slug for item in items]
    if len(slugs) != len(set(slugs)):
        report.errors.append(f"{source_name}: tópicos duplicados no arquivo")
        return

    for data in items:
        topic = topics.get(data.slug)
        if topic is None:
            topic = Topic(slug=data.slug)
            db.add(topic)
            topics[data.slug] = topic
        topic.name = data.name
        topic.description = data.description
        topic.position = data.position
    db.flush()

    for data in items:
        topic = topics[data.slug]
        if data.parent:
            parent = topics.get(data.parent)
            if parent is None:
                report.errors.append(
                    f"{source_name}: tópico pai '{data.parent}' não encontrado para '{data.slug}'"
                )
                topic.parent_id = None
            else:
                topic.parent_id = parent.id
        else:
            topic.parent_id = None
    db.flush()


def upsert_exams(
    db: Session,
    exams: dict[str, Exam],
    items,
    source_name: str,
    report: ImportReport,
) -> None:
    slugs = [item.slug for item in items]
    if len(slugs) != len(set(slugs)):
        report.errors.append(f"{source_name}: concursos duplicados no arquivo")
        return

    for data in items:
        exam = exams.get(data.slug)
        if exam is None:
            exam = Exam(slug=data.slug)
            db.add(exam)
            exams[data.slug] = exam
        exam.name = data.name
        exam.organization = data.organization
        exam.year = data.year
        exam.role = data.role
        exam.edital = data.edital
        exam.source_url = data.source_url
        exam.answer_key_url = data.answer_key_url
    db.flush()


def _tags_map(db: Session) -> dict[str, Tag]:
    return {tag.slug: tag for tag in db.scalars(select(Tag)).all()}


def upsert_tags(
    db: Session,
    tags: dict[str, Tag],
    items,
    source_name: str,
    report: ImportReport,
) -> None:
    slugs = [item.slug for item in items]
    if len(slugs) != len(set(slugs)):
        report.errors.append(f"{source_name}: tags duplicadas no arquivo")
        return
    for data in items:
        tag = tags.get(data.slug)
        if tag is None:
            tag = Tag(slug=data.slug)
            db.add(tag)
            tags[data.slug] = tag
        tag.name = data.name
        tag.area = data.area
        tag.position = data.position
        tag.description = data.description
    db.flush()


def import_payload(
    db: Session,
    payload: QuestionFile,
    default_status: ReviewStatus = ReviewStatus.approved,
    source_name: str = "payload",
) -> ImportReport:
    report = ImportReport(files=1)
    topics = _topics_map(db)
    exams = _exams_map(db)
    tags = _tags_map(db)

    try:
        upsert_topics(db, topics, payload.topics, source_name, report)
        upsert_exams(db, exams, payload.exams, source_name, report)
        db.flush()

        seen_external_ids: set[str] = set()
        seen_hashes: dict[str, str] = {}

        for question_data in payload.questions:
            label = question_data.external_id
            if label in seen_external_ids:
                report.errors.append(
                    f"{source_name} [{label}]: external_id duplicado no arquivo"
                )
                report.skipped += 1
                continue
            seen_external_ids.add(label)

            status = question_data.review_status or default_status
            errors = _completeness_errors(question_data, status)
            if errors:
                report.errors.extend(
                    f"{source_name} [{label}]: {error}" for error in errors
                )
                report.skipped += 1
                continue

            topic = topics.get(question_data.topic)
            if topic is None:
                report.errors.append(
                    f"{source_name} [{label}]: tópico '{question_data.topic}' não encontrado"
                )
                report.skipped += 1
                continue

            exam = None
            if question_data.exam:
                exam = exams.get(question_data.exam)
                if exam is None:
                    report.errors.append(
                        f"{source_name} [{label}]: concurso '{question_data.exam}' não encontrado"
                    )
                    report.skipped += 1
                    continue

            tag = tags.get(question_data.tag)
            if tag is None:
                report.errors.append(
                    f"{source_name} [{label}]: tag '{question_data.tag}' não encontrada no catálogo"
                )
                report.skipped += 1
                continue

            hashed = content_hash(question_data)
            other_external_id = seen_hashes.get(hashed)
            if other_external_id and other_external_id != label:
                report.errors.append(
                    f"{source_name} [{label}]: conteúdo duplicado de '{other_external_id}'"
                )
                report.skipped += 1
                continue
            seen_hashes[hashed] = label

            existing = db.scalar(
                select(Question).where(Question.external_id == label)
            )
            duplicate = db.scalar(
                select(Question).where(
                    Question.content_hash == hashed,
                    Question.external_id != label,
                )
            )
            if duplicate is not None:
                report.errors.append(
                    f"{source_name} [{label}]: conteúdo duplicado de '{duplicate.external_id}'"
                )
                report.skipped += 1
                continue

            try:
                with db.begin_nested():
                    if existing is None:
                        question = Question(external_id=label)
                        db.add(question)
                        created = True
                    else:
                        question = existing
                        created = False

                    question.topic_id = topic.id
                    question.exam_id = exam.id if exam else None
                    question.tag_id = tag.id
                    question.type = question_data.type
                    question.statement = question_data.statement
                    question.context = question_data.context
                    question.media_url = question_data.media_url
                    question.context_media_url = question_data.context_media_url
                    question.difficulty = question_data.difficulty
                    question.source = question_data.source
                    question.source_url = question_data.source_url
                    question.source_question_number = (
                        question_data.source_question_number
                    )
                    question.general_explanation = question_data.general_explanation
                    question.origin = question_data.origin
                    question.answer_source = question_data.answer_source
                    question.explanation_source = question_data.explanation_source
                    question.review_status = status
                    question.content_hash = hashed

                    existing_alternatives = {alt.label: alt for alt in question.alternatives}
                    incoming_labels = set()
                    for position, alternative_data in enumerate(
                        question_data.alternatives, start=1
                    ):
                        incoming_labels.add(alternative_data.label)
                        alternative = existing_alternatives.get(alternative_data.label)
                        if alternative is None:
                            alternative = Alternative(
                                label=alternative_data.label,
                                question=question,
                            )
                            db.add(alternative)
                        alternative.text = alternative_data.text
                        alternative.is_correct = alternative_data.is_correct
                        alternative.explanation = alternative_data.explanation
                        alternative.media_url = alternative_data.media_url
                        alternative.position = position
                        alternative.is_active = True

                    for label_name, alternative in existing_alternatives.items():
                        if label_name not in incoming_labels:
                            alternative.is_active = False

                    db.flush()

                if created:
                    report.created += 1
                else:
                    report.updated += 1
            except Exception as exc:
                report.errors.append(
                    f"{source_name} [{label}]: falha ao importar — {_format_error(exc)}"
                )
                report.skipped += 1

        db.commit()
    except Exception as exc:
        db.rollback()
        report.errors.append(f"{source_name}: falha na importação — {_format_error(exc)}")

    return report


def import_catalog(db: Session, catalog_dir: Path) -> ImportReport:
    report = ImportReport()
    topics_path = catalog_dir / "topics.json"
    exams_path = catalog_dir / "exams.json"

    if not catalog_dir.exists():
        return report

    if topics_path.exists():
        report.files += 1
        try:
            raw = json.loads(topics_path.read_text(encoding="utf-8"))
            payload = TopicCatalog.model_validate(raw)
            topics = _topics_map(db)
            upsert_topics(db, topics, payload.topics, topics_path.name, report)
            db.commit()
        except Exception as exc:
            db.rollback()
            report.errors.append(f"{topics_path.name}: {_format_error(exc)}")

    if exams_path.exists():
        report.files += 1
        try:
            raw = json.loads(exams_path.read_text(encoding="utf-8"))
            payload = ExamCatalog.model_validate(raw)
            exams = _exams_map(db)
            upsert_exams(db, exams, payload.exams, exams_path.name, report)
            db.commit()
        except Exception as exc:
            db.rollback()
            report.errors.append(f"{exams_path.name}: {_format_error(exc)}")

    tags_path = catalog_dir / "tags.json"
    if tags_path.exists():
        report.files += 1
        try:
            raw = json.loads(tags_path.read_text(encoding="utf-8"))
            payload = TagCatalog.model_validate(raw)
            tags = _tags_map(db)
            upsert_tags(db, tags, payload.tags, tags_path.name, report)
            db.commit()
        except Exception as exc:
            db.rollback()
            report.errors.append(f"{tags_path.name}: {_format_error(exc)}")

    return report


def import_file(
    db: Session,
    path: Path,
    default_status: ReviewStatus = ReviewStatus.approved,
) -> ImportReport:
    report = ImportReport(files=1)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        payload = QuestionFile.model_validate(raw)
    except json.JSONDecodeError as exc:
        report.errors.append(f"{path.name}: JSON inválido — {exc.msg} (linha {exc.lineno})")
        return report
    except ValidationError as exc:
        report.errors.append(f"{path.name}: {_format_error(exc)}")
        return report
    except OSError as exc:
        report.errors.append(f"{path.name}: não foi possível ler o arquivo — {exc}")
        return report

    imported = import_payload(
        db, payload, default_status=default_status, source_name=path.name
    )
    imported.files = 0
    report.merge(imported)
    return report


def import_directory(
    db: Session,
    directory: Path,
    default_status: ReviewStatus = ReviewStatus.approved,
) -> ImportReport:
    report = ImportReport()
    if not directory.exists():
        report.errors.append(f"diretório não encontrado: {directory}")
        return report
    for path in sorted(directory.rglob("*.json")):
        report.merge(import_file(db, path, default_status=default_status))
    return report


def import_all(
    db: Session,
    questions_dir: Path,
    catalog_dir: Path,
    default_status: ReviewStatus = ReviewStatus.approved,
) -> ImportReport:
    report = import_catalog(db, catalog_dir)
    report.merge(
        import_directory(db, questions_dir, default_status=default_status)
    )
    return report
