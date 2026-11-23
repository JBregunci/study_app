from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..models import Exam, Material, Question, Tag
from ..utils import slugify
from . import question_bank


@dataclass
class AuditReport:
    counts: dict[str, int] = field(default_factory=dict)
    critical: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_critical(self, message: str) -> None:
        self.critical.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def ok(self) -> bool:
        return not self.critical


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.lower()
    return re.sub(r"[^a-z0-9]+", " ", ascii_value).strip()


def normalized_question_key(question: Question) -> str:
    alternatives = sorted(
        (alternative.label, alternative.text)
        for alternative in question.alternatives
        if alternative.is_active
    )
    payload = normalize_text(question.statement) + "|" + "|".join(
        f"{label}:{normalize_text(text)}" for label, text in alternatives
    )
    return payload


def exam_key(exam: Exam) -> str:
    agency = getattr(exam, "agency", "") or exam.name
    contest_key = getattr(exam, "contest_key", "")
    return "|".join(
        [
            normalize_text(agency),
            normalize_text(exam.organization),
            str(exam.year or ""),
            normalize_text(exam.role),
            normalize_text(exam.edital),
            normalize_text(contest_key),
        ]
    )


def _check_media(report: AuditReport, questions: list[Question]) -> None:
    media_root = Path("data/media")
    for question in questions:
        for url in (question.media_url, question.context_media_url):
            if not url:
                continue
            relative = url.removeprefix("/media/")
            path = media_root / relative
            if not path.exists():
                report.add_critical(
                    f"mídia ausente: {url} (questão {question.external_id})"
                )


def audit_database(db: Session) -> AuditReport:
    report = AuditReport()
    questions = list(
        db.scalars(
            select(Question).options(
                selectinload(Question.alternatives),
                joinedload(Question.topic),
                joinedload(Question.tag),
                joinedload(Question.exam),
            )
        ).unique().all()
    )
    materials = list(
        db.scalars(
            select(Material).options(
                selectinload(Material.topics),
                selectinload(Material.tags),
            )
        ).unique().all()
    )
    tags = list(db.scalars(select(Tag)).all())
    exams = list(db.scalars(select(Exam)).all())

    report.counts = {
        "questões": len(questions),
        "materiais": len(materials),
        "tags": len(tags),
        "exames": len(exams),
    }

    by_hash: dict[str, list[Question]] = {}
    by_normalized: dict[str, list[Question]] = {}
    for question in questions:
        by_hash.setdefault(question.content_hash, []).append(question)
        by_normalized.setdefault(normalized_question_key(question), []).append(question)

    for hash_value, group in by_hash.items():
        if len(group) > 1:
            report.add_critical(
                f"content_hash duplicado {hash_value[:12]} em "
                + ", ".join(item.external_id for item in group)
            )

    for group in by_normalized.values():
        if len(group) > 1:
            report.add_critical(
                "questões normalizadas duplicadas: "
                + ", ".join(item.external_id for item in group)
            )

    by_exam: dict[str, list[Exam]] = {}
    for exam in exams:
        key = exam_key(exam)
        if key.strip("|"):
            by_exam.setdefault(key, []).append(exam)
    for group in by_exam.values():
        if len(group) > 1:
            report.add_critical(
                "exames duplicados: " + ", ".join(item.slug for item in group)
            )

    tag_names: dict[str, list[Tag]] = {}
    for tag in tags:
        tag_names.setdefault(normalize_text(tag.name), []).append(tag)
    for group in tag_names.values():
        if len(group) > 1:
            report.add_critical(
                "tags com mesmo nome normalizado: "
                + ", ".join(item.slug for item in group)
            )

    material_slugs: dict[str, list[Material]] = {}
    for material in materials:
        material_slugs.setdefault(material.slug, []).append(material)
    for group in material_slugs.values():
        if len(group) > 1:
            report.add_critical(
                "materiais duplicados: " + ", ".join(item.slug for item in group)
            )

    for question in questions:
        if question.tag_id is None:
            report.add_critical(f"questão sem assunto: {question.external_id}")
        if question.topic_id is None:
            report.add_critical(f"questão sem tema: {question.external_id}")
        if not question_bank.related_materials(db, question, limit=1):
            report.add_critical(f"questão sem material relacionado: {question.external_id}")

    for material in materials:
        if not material.topics:
            report.add_critical(f"material sem temas: {material.slug}")

    _check_media(report, questions)
    return report


def audit_sources(
    questions_dir: Path,
    catalog_dir: Path,
    materials_dir: Path,
) -> AuditReport:
    report = AuditReport()
    external_ids: dict[str, list[str]] = {}
    for path in sorted(questions_dir.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            report.add_critical(f"JSON inválido em {path}: {exc}")
            continue
        for question in payload.get("questions", []):
            external_id = question.get("external_id", "")
            external_ids.setdefault(external_id, []).append(str(path))
    for external_id, files in external_ids.items():
        if len(files) > 1:
            report.add_critical(
                f"external_id duplicado '{external_id}': " + ", ".join(files)
            )

    exams_path = catalog_dir / "exams.json"
    if exams_path.exists():
        try:
            payload = json.loads(exams_path.read_text(encoding="utf-8"))
            seen_exams: dict[str, list[str]] = {}
            for exam in payload.get("exams", []):
                key = "|".join(
                    [
                        normalize_text(exam.get("agency", "") or exam.get("name", "")),
                        normalize_text(exam.get("organization", "")),
                        str(exam.get("year", "")),
                        normalize_text(exam.get("role", "")),
                        normalize_text(exam.get("edital", "")),
                        normalize_text(exam.get("contest_key", "")),
                    ]
                )
                if key.strip("|"):
                    seen_exams.setdefault(key, []).append(exam.get("slug", "?"))
            for slugs in seen_exams.values():
                if len(slugs) > 1:
                    report.add_critical(
                        "exames duplicados em exams.json: " + ", ".join(slugs)
                    )
        except Exception as exc:
            report.add_critical(f"exams.json inválido: {exc}")

    tags_path = catalog_dir / "tags.json"
    if tags_path.exists():
        try:
            payload = json.loads(tags_path.read_text(encoding="utf-8"))
            slugs = [item["slug"] for item in payload.get("tags", [])]
            normalized = [normalize_text(item["name"]) for item in payload.get("tags", [])]
            if len(slugs) != len(set(slugs)):
                report.add_critical("slugs duplicados em tags.json")
            if len(normalized) != len(set(normalized)):
                report.add_critical("nomes de tags duplicados em tags.json")
        except Exception as exc:
            report.add_critical(f"tags.json inválido: {exc}")

    material_slugs: dict[str, list[str]] = {}
    for path in sorted(materials_dir.rglob("*.md")):
        try:
            post = frontmatter.load(path)
            slug = post.metadata.get("slug") or slugify(path.stem)
            material_slugs.setdefault(slug, []).append(str(path))
        except Exception as exc:
            report.add_critical(f"material inválido em {path}: {exc}")
    for slug, files in material_slugs.items():
        if len(files) > 1:
            report.add_critical(
                f"material duplicado '{slug}': " + ", ".join(files)
            )

    return report


def print_report(report: AuditReport) -> None:
    print("Auditoria da biblioteca")
    for name, value in report.counts.items():
        print(f"- {name}: {value}")
    if report.critical:
        print("\nCRÍTICO:")
        for message in report.critical:
            print(f"- {message}")
    if report.warnings:
        print("\nAVISOS:")
        for message in report.warnings:
            print(f"- {message}")
    if report.ok:
        print("\nOK: nenhuma duplicidade ou inconsistência crítica encontrada.")
    else:
        print(f"\nFALHOU: {len(report.critical)} problema(s) crítico(s).")
