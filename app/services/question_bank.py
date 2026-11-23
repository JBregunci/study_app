from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..models import (
    Attempt,
    Difficulty,
    Exam,
    Material,
    Question,
    QuestionType,
    ReviewStatus,
    Tag,
    Topic,
)


@dataclass
class AttemptDot:
    id: int
    is_correct: bool
    timed_out: bool
    answered_at: datetime
    time_spent_seconds: int


@dataclass
class QuestionPerformance:
    total: int = 0
    correct: int = 0
    blank: int = 0
    total_seconds: int = 0
    last_attempt_at: datetime | None = None
    dots: list[AttemptDot | None] = field(default_factory=lambda: [None] * 5)

    @property
    def incorrect(self) -> int:
        return max(0, self.total - self.correct - self.blank)

    @property
    def accuracy(self) -> float | None:
        if not self.total:
            return None
        return self.correct * 100 / self.total

    @property
    def avg_seconds(self) -> float | None:
        if not self.total:
            return None
        return self.total_seconds / self.total


@dataclass
class QuestionRow:
    question: Question
    performance: QuestionPerformance


@dataclass
class QuestionListResult:
    rows: list[QuestionRow]
    total: int
    page: int
    per_page: int

    @property
    def total_pages(self) -> int:
        if self.per_page <= 0:
            return 1
        return max(1, (self.total + self.per_page - 1) // self.per_page)

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages


def performance_for_questions(
    db: Session, question_ids: list[int]
) -> dict[int, QuestionPerformance]:
    if not question_ids:
        return {}

    performances = {question_id: QuestionPerformance() for question_id in question_ids}
    rows = db.execute(
        select(
            Attempt.question_id,
            func.count(Attempt.id),
            func.coalesce(
                func.sum(case((Attempt.is_correct.is_(True), 1), else_=0)), 0
            ),
            func.coalesce(
                func.sum(
                    case((Attempt.selected_alternative_id.is_(None), 1), else_=0)
                ),
                0,
            ),
            func.coalesce(func.sum(Attempt.time_spent_seconds), 0),
            func.max(Attempt.answered_at),
        )
        .where(Attempt.question_id.in_(question_ids))
        .group_by(Attempt.question_id)
    ).all()
    for row in rows:
        perf = performances[row[0]]
        perf.total = int(row[1] or 0)
        perf.correct = int(row[2] or 0)
        perf.blank = int(row[3] or 0)
        perf.total_seconds = int(row[4] or 0)
        perf.last_attempt_at = row[5]

    rn = func.row_number().over(
        partition_by=Attempt.question_id,
        order_by=(Attempt.answered_at.desc(), Attempt.id.desc()),
    ).label("rn")
    recent = (
        select(
            Attempt.id.label("id"),
            Attempt.question_id.label("question_id"),
            Attempt.is_correct.label("is_correct"),
            Attempt.timed_out.label("timed_out"),
            Attempt.answered_at.label("answered_at"),
            Attempt.time_spent_seconds.label("time_spent_seconds"),
            rn,
        )
        .where(Attempt.question_id.in_(question_ids))
        .subquery()
    )
    recent_rows = db.execute(
        select(recent)
        .where(recent.c.rn <= 5)
        .order_by(recent.c.question_id, recent.c.answered_at.desc(), recent.c.id.desc())
    ).all()
    by_question: dict[int, list[AttemptDot]] = {}
    for row in recent_rows:
        by_question.setdefault(row.question_id, []).append(
            AttemptDot(
                id=row.id,
                is_correct=bool(row.is_correct),
                timed_out=bool(row.timed_out),
                answered_at=row.answered_at,
                time_spent_seconds=row.time_spent_seconds,
            )
        )
    for question_id, dots in by_question.items():
        oldest_first = list(reversed(dots[:5]))
        performances[question_id].dots = [None] * (5 - len(oldest_first)) + oldest_first
    return performances


def topic_map(db: Session) -> dict[str, Topic]:
    return {topic.slug: topic for topic in db.scalars(select(Topic)).all()}


def descendant_topic_ids(db: Session, slug: str) -> set[int]:
    topics = list(db.scalars(select(Topic)).all())
    by_slug = {topic.slug: topic for topic in topics}
    root = by_slug.get(slug)
    if root is None:
        return set()
    children: dict[int | None, list[Topic]] = {}
    for topic in topics:
        children.setdefault(topic.parent_id, []).append(topic)
    result = set()
    stack = [root]
    while stack:
        current = stack.pop()
        result.add(current.id)
        stack.extend(children.get(current.id, []))
    return result


def topic_options(db: Session) -> list[dict]:
    topics = list(db.scalars(select(Topic)).all())
    children: dict[int | None, list[Topic]] = {}
    for topic in topics:
        children.setdefault(topic.parent_id, []).append(topic)
    for values in children.values():
        values.sort(key=lambda item: (item.position, item.name))

    result = []

    def walk(parent_id, depth):
        for topic in children.get(parent_id, []):
            result.append({"topic": topic, "depth": depth})
            walk(topic.id, depth + 1)

    walk(None, 0)
    return result


def topic_breadcrumb(topic: Topic | None) -> list[Topic]:
    if topic is None:
        return []
    chain = []
    current = topic
    seen = set()
    while current is not None and current.id not in seen:
        seen.add(current.id)
        chain.append(current)
        current = current.parent
    return list(reversed(chain))


def filter_options(db: Session) -> dict:
    exams = list(
        db.scalars(
            select(Exam).order_by(Exam.year.desc().nullslast(), Exam.name)
        ).all()
    )
    organizations = list(
        db.scalars(
            select(Exam.organization)
            .where(Exam.organization != "")
            .distinct()
            .order_by(Exam.organization)
        ).all()
    )
    years = list(
        db.scalars(
            select(Exam.year)
            .where(Exam.year.is_not(None))
            .distinct()
            .order_by(Exam.year.desc())
        ).all()
    )
    tag_rows = db.execute(
        select(Tag, func.count(Question.id).label("total"))
        .select_from(Tag)
        .join(Question, Question.tag_id == Tag.id)
        .where(Question.review_status == ReviewStatus.approved)
        .group_by(Tag.id)
        .order_by(Tag.position, Tag.name)
    ).all()
    areas = list(
        db.scalars(
            select(Tag.area).distinct().order_by(Tag.area)
        ).all()
    )
    return {
        "topics": topic_options(db),
        "exams": exams,
        "organizations": organizations,
        "years": years,
        "areas": areas,
        "tags": [{"tag": row[0], "total": int(row[1])} for row in tag_rows],
    }


def _filtered_questions_stmt(
    db: Session,
    q: str = "",
    topic: str = "",
    exam: str = "",
    organization: str = "",
    year: str = "",
    role: str = "",
    question_type: str = "",
    difficulty: str = "",
    tag: str = "",
    area: str = "",
    situation: str = "",
    order: str = "recent",
):
    stmt = select(Question).where(Question.review_status == ReviewStatus.approved)
    needs_exam_join = False

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Question.statement.ilike(like),
                Question.context.ilike(like),
                Question.external_id.ilike(like),
                Question.tag.has(Tag.name.ilike(like)),
            )
        )
    if topic:
        ids = descendant_topic_ids(db, topic)
        stmt = stmt.where(Question.topic_id.in_(ids or {-1}))
    if exam:
        needs_exam_join = True
        stmt = stmt.where(Exam.slug == exam)
    if organization:
        needs_exam_join = True
        stmt = stmt.where(Exam.organization == organization)
    if year:
        needs_exam_join = True
        stmt = stmt.where(Exam.year == int(year))
    if role:
        needs_exam_join = True
        stmt = stmt.where(Exam.role.ilike(f"%{role}%"))
    if question_type:
        stmt = stmt.where(Question.type == QuestionType(question_type))
    if difficulty:
        stmt = stmt.where(Question.difficulty == Difficulty(difficulty))
    if tag:
        stmt = stmt.where(Question.tag.has(Tag.slug == tag))
    if area:
        stmt = stmt.where(Question.tag.has(Tag.area == area))
    if situation == "unseen":
        stmt = stmt.where(
            ~exists(
                select(Attempt.id).where(Attempt.question_id == Question.id)
            )
        )
    elif situation == "error":
        stmt = stmt.where(
            exists(
                select(Attempt.id).where(
                    Attempt.question_id == Question.id,
                    Attempt.is_correct.is_(False),
                )
            )
        )

    if needs_exam_join:
        stmt = stmt.join(Exam, Question.exam_id == Exam.id)

    attempt_count = (
        select(func.count(Attempt.id))
        .where(Attempt.question_id == Question.id)
        .correlate(Question)
        .scalar_subquery()
    )
    wrong_count = (
        select(func.count(Attempt.id))
        .where(
            Attempt.question_id == Question.id,
            Attempt.is_correct.is_(False),
        )
        .correlate(Question)
        .scalar_subquery()
    )
    if order == "errors":
        stmt = stmt.order_by(wrong_count.desc(), Question.id.desc())
    elif order == "unseen":
        stmt = stmt.order_by(attempt_count.asc(), Question.id.desc())
    else:
        stmt = stmt.order_by(Question.id.desc())
    return stmt


def list_questions(
    db: Session,
    page: int = 1,
    per_page: int = 25,
    **filters,
) -> QuestionListResult:
    page = max(1, page)
    per_page = max(1, min(per_page, 100))
    stmt = _filtered_questions_stmt(db, **filters)
    total = int(
        db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
        or 0
    )
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)
    questions = list(
        db.scalars(
            stmt.options(
                joinedload(Question.topic),
                joinedload(Question.exam),
                joinedload(Question.tag),
            )
            .limit(per_page)
            .offset((page - 1) * per_page)
        ).unique().all()
    )
    performances = performance_for_questions(db, [question.id for question in questions])
    rows = [
        QuestionRow(question=question, performance=performances[question.id])
        for question in questions
    ]
    return QuestionListResult(
        rows=rows, total=total, page=page, per_page=per_page
    )


def get_question(db: Session, question_id: int) -> Question | None:
    return db.scalar(
        select(Question)
        .options(
            joinedload(Question.topic),
            joinedload(Question.exam),
            joinedload(Question.tag),
            selectinload(Question.alternatives),
        )
        .where(Question.id == question_id)
    )


def question_attempts(db: Session, question_id: int, limit: int = 50):
    return list(
        db.scalars(
            select(Attempt)
            .options(joinedload(Attempt.selected_alternative))
            .where(Attempt.question_id == question_id)
            .order_by(Attempt.answered_at.desc(), Attempt.id.desc())
            .limit(limit)
        ).all()
    )


def _ancestor_topic_ids(topic: Topic) -> set[int]:
    result = set()
    current = topic
    seen = set()
    while current is not None and current.id not in seen:
        seen.add(current.id)
        result.add(current.id)
        current = current.parent
    return result


def _material_matches_question(
    material: Material,
    question: Question,
    ancestor_ids: set[int],
) -> bool:
    topic_ids = {topic.id for topic in material.topics}
    if not topic_ids.intersection(ancestor_ids):
        return False
    if material.tags and question.tag_id not in {tag.id for tag in material.tags}:
        return False
    return True


def related_materials(
    db: Session, question: Question, limit: int = 5
) -> list[Material]:
    ancestor_ids = _ancestor_topic_ids(question.topic)
    materials = list(
        db.scalars(
            select(Material)
            .where(Material.review_status == ReviewStatus.approved)
            .options(
                selectinload(Material.topics),
                selectinload(Material.tags),
            )
            .order_by(Material.updated_at.desc())
        ).unique().all()
    )
    matches = [
        material
        for material in materials
        if _material_matches_question(material, question, ancestor_ids)
    ]
    matches.sort(key=lambda material: (len(material.tags), len(material.topics), -material.id))
    return matches[:limit]


def recommended_materials_for_session(
    db: Session, questions: list[Question], limit: int = 6
) -> list[Material]:
    seen: set[int] = set()
    result: list[Material] = []
    for question in questions:
        for material in related_materials(db, question, limit=4):
            if material.id not in seen:
                seen.add(material.id)
                result.append(material)
    result.sort(key=lambda material: (len(material.tags), len(material.topics), -material.id))
    return result[:limit]


def exam_rows(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            Exam,
            func.count(Question.id).label("total"),
        )
        .join(Question, and_(Question.exam_id == Exam.id, Question.review_status == ReviewStatus.approved))
        .group_by(Exam.id)
        .order_by(Exam.year.desc().nullslast(), Exam.name)
    ).all()
    return [{"exam": row[0], "total": int(row[1])} for row in rows]


def related_questions_for_material(
    db: Session, material: Material, limit: int = 60
) -> list[QuestionRow]:
    questions = list(
        db.scalars(
            select(Question)
            .where(Question.review_status == ReviewStatus.approved)
            .options(
                joinedload(Question.topic),
                joinedload(Question.exam),
                joinedload(Question.tag),
            )
            .order_by(Question.id)
        ).unique().all()
    )
    material_tag_ids = {tag.id for tag in material.tags}
    material_topic_ids = {topic.id for topic in material.topics}
    matched = []
    for question in questions:
        ancestor_ids = _ancestor_topic_ids(question.topic)
        if not material_topic_ids.intersection(ancestor_ids):
            continue
        if material_tag_ids and question.tag_id not in material_tag_ids:
            continue
        matched.append(question)
        if len(matched) >= limit:
            break
    performances = performance_for_questions(db, [question.id for question in matched])
    return [
        QuestionRow(question=question, performance=performances[question.id])
        for question in matched
    ]


def materials_for_topics(
    db: Session, topic_ids: set[int], limit: int = 8
) -> list[Material]:
    if not topic_ids:
        return []
    return list(
        db.scalars(
            select(Material)
            .where(
                Material.topics.any(Topic.id.in_(topic_ids)),
                Material.review_status == ReviewStatus.approved,
            )
            .options(
                selectinload(Material.topics),
                selectinload(Material.tags),
            )
            .order_by(Material.updated_at.desc())
            .limit(limit)
        ).unique().all()
    )


def exam_question_count(db: Session, exam_id: int) -> int:
    return int(
        db.scalar(
            select(func.count(Question.id)).where(
                Question.exam_id == exam_id,
                Question.review_status == ReviewStatus.approved,
            )
        )
        or 0
    )


def exam_tag_options(db: Session, exam_id: int) -> list[dict]:
    rows = db.execute(
        select(Tag, func.count(Question.id).label("total"))
        .select_from(Tag)
        .join(Question, Question.tag_id == Tag.id)
        .where(
            Question.review_status == ReviewStatus.approved,
            Question.exam_id == exam_id,
        )
        .group_by(Tag.id)
        .order_by(func.count(Question.id).desc(), Tag.name)
    ).all()
    return [{"tag": row[0], "total": int(row[1])} for row in rows]
