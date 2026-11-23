from __future__ import annotations

from pathlib import Path

import frontmatter
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Material, Tag, Topic
from ..schemas import MaterialMeta
from ..utils import slugify
from .question_import import ImportReport, _format_error


def import_material_file(
    db: Session,
    path: Path,
    source_name: str | None = None,
) -> ImportReport:
    report = ImportReport(files=1)
    name = source_name or path.name
    try:
        post = frontmatter.load(path)
        metadata = MaterialMeta.model_validate(post.metadata)
    except ValidationError as exc:
        report.errors.append(f"{name}: {_format_error(exc)}")
        return report
    except Exception as exc:
        report.errors.append(f"{name}: não foi possível ler o material — {exc}")
        return report

    slug = metadata.slug or slugify(path.stem)
    if not metadata.topics:
        report.errors.append(f"{name}: informe pelo menos um tópico em 'topics'")
        return report

    topic_slugs = {topic.slug: topic for topic in db.scalars(select(Topic)).all()}
    topics = []
    for topic_slug in metadata.topics:
        topic = topic_slugs.get(topic_slug)
        if topic is None:
            report.errors.append(f"{name}: tópico '{topic_slug}' não encontrado")
            return report
        topics.append(topic)

    tag_slugs = {tag.slug: tag for tag in db.scalars(select(Tag)).all()}
    tags = []
    for tag_slug in metadata.tags:
        tag = tag_slugs.get(tag_slug)
        if tag is None:
            report.errors.append(f"{name}: tag '{tag_slug}' não encontrada no catálogo")
            return report
        tags.append(tag)

    material = db.scalar(select(Material).where(Material.slug == slug))
    created = material is None
    if material is None:
        material = Material(slug=slug)
        db.add(material)

    material.title = metadata.title
    material.summary = metadata.summary
    material.body_md = post.content
    material.source = metadata.source
    material.source_url = metadata.source_url
    material.source_kind = metadata.source_kind
    material.review_status = metadata.review_status
    material.topics = topics
    material.tags = tags

    try:
        db.commit()
        if created:
            report.created += 1
        else:
            report.updated += 1
    except Exception as exc:
        db.rollback()
        report.errors.append(f"{name}: falha ao importar — {_format_error(exc)}")

    return report


def import_materials_directory(db: Session, directory: Path) -> ImportReport:
    report = ImportReport()
    if not directory.exists():
        return report
    for path in sorted(directory.rglob("*.md")):
        report.merge(import_material_file(db, path, str(path.relative_to(directory))))
    return report
