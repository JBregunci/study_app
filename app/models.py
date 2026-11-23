from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .utils import local_today, utc_now


class QuestionType(str, Enum):
    single_choice = "single_choice"
    true_false = "true_false"


class Difficulty(str, Enum):
    facil = "facil"
    medio = "medio"
    dificil = "dificil"


class ReviewStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    archived = "archived"


class SessionMode(str, Enum):
    sequential = "sequential"
    random = "random"
    set = "set"
    retry = "retry"


class FeedbackMode(str, Enum):
    immediate = "immediate"
    end = "end"


class SessionStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class QuestionOrigin(str, Enum):
    official = "official"
    derived = "derived"
    authored = "authored"


class AnswerSource(str, Enum):
    official_key = "official_key"
    manual = "manual"
    generated = "generated"


class SourceKind(str, Enum):
    manual = "manual"
    official = "official"
    generated = "generated"


def enum_column(enum_type, length: int = 32):
    return SAEnum(
        enum_type,
        native_enum=False,
        values_callable=lambda cls: [item.value for item in cls],
        length=length,
        validate_strings=True,
    )


question_exams = Table(
    "question_exams",
    Base.metadata,
    Column(
        "question_id",
        ForeignKey("questions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "exam_id",
        ForeignKey("exams.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

material_topics = Table(
    "material_topics",
    Base.metadata,
    Column(
        "material_id",
        ForeignKey("materials.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topic_id",
        ForeignKey("topics.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

material_tags = Table(
    "material_tags",
    Base.metadata,
    Column(
        "material_id",
        ForeignKey("materials.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    parent: Mapped[Topic | None] = relationship(remote_side=[id])
    questions: Mapped[list[Question]] = relationship(back_populates="topic")
    materials: Mapped[list[Material]] = relationship(
        secondary=material_topics,
        back_populates="topics",
    )


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    organization: Mapped[str] = mapped_column(String(120), default="", nullable=False, index=True)
    agency: Mapped[str] = mapped_column(String(120), default="", nullable=False, index=True)
    contest_key: Mapped[str] = mapped_column(String(160), default="", nullable=False, index=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(180), default="", nullable=False)
    edital: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    answer_key_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    questions: Mapped[list[Question]] = relationship(back_populates="exam")
    linked_questions: Mapped[list[Question]] = relationship(
        secondary=question_exams,
        back_populates="exams",
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    area: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    questions: Mapped[list[Question]] = relationship(back_populates="tag")
    materials: Mapped[list[Material]] = relationship(
        secondary=material_tags, back_populates="tags"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(
        String(180), unique=True, nullable=False, index=True
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    exam_id: Mapped[int | None] = mapped_column(
        ForeignKey("exams.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    type: Mapped[QuestionType] = mapped_column(
        enum_column(QuestionType), nullable=False
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, default="", nullable=False)
    media_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    context_media_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    difficulty: Mapped[Difficulty | None] = mapped_column(
        enum_column(Difficulty), nullable=True
    )
    source: Mapped[str] = mapped_column(String(260), default="", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1200), nullable=True)
    source_question_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    general_explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    origin: Mapped[QuestionOrigin] = mapped_column(
        enum_column(QuestionOrigin), default=QuestionOrigin.authored, nullable=False
    )
    answer_source: Mapped[AnswerSource] = mapped_column(
        enum_column(AnswerSource), default=AnswerSource.manual, nullable=False
    )
    explanation_source: Mapped[SourceKind] = mapped_column(
        enum_column(SourceKind), default=SourceKind.manual, nullable=False
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        enum_column(ReviewStatus), default=ReviewStatus.draft, nullable=False, index=True
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    topic: Mapped[Topic] = relationship(back_populates="questions")
    exam: Mapped[Exam | None] = relationship(back_populates="questions")
    exams: Mapped[list[Exam]] = relationship(
        secondary=question_exams,
        back_populates="linked_questions",
        order_by="Exam.name",
    )
    alternatives: Mapped[list[Alternative]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="Alternative.position",
    )
    tag: Mapped[Tag] = relationship(back_populates="questions")


class Alternative(Base):
    __tablename__ = "alternatives"
    __table_args__ = (UniqueConstraint("question_id", "label", name="uq_alt_question_label"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(8), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    media_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    question: Mapped[Question] = relationship(back_populates="alternatives")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(260), default="", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1200), nullable=True)
    source_kind: Mapped[SourceKind] = mapped_column(
        enum_column(SourceKind), default=SourceKind.manual, nullable=False
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        enum_column(ReviewStatus), default=ReviewStatus.approved, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    topics: Mapped[list[Topic]] = relationship(
        secondary=material_topics,
        back_populates="materials",
        order_by="Topic.position",
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary=material_tags,
        back_populates="materials",
        order_by="Tag.name",
    )


class QuestionSet(Base):
    __tablename__ = "question_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    exam_id: Mapped[int | None] = mapped_column(
        ForeignKey("exams.id", ondelete="SET NULL"), nullable=True
    )
    target_title: Mapped[str] = mapped_column(String(220), default="", nullable=False)
    default_feedback_mode: Mapped[FeedbackMode] = mapped_column(
        enum_column(FeedbackMode), default=FeedbackMode.end, nullable=False
    )
    default_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    exam: Mapped[Exam | None] = relationship()
    items: Mapped[list[QuestionSetItem]] = relationship(
        back_populates="question_set",
        cascade="all, delete-orphan",
        order_by="QuestionSetItem.position",
    )


class QuestionSetItem(Base):
    __tablename__ = "question_set_items"
    __table_args__ = (
        UniqueConstraint("set_id", "position", name="uq_set_item_position"),
        UniqueConstraint("set_id", "question_id", name="uq_set_item_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    set_id: Mapped[int] = mapped_column(
        ForeignKey("question_sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    question_set: Mapped[QuestionSet] = relationship(back_populates="items")
    question: Mapped[Question] = relationship()


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(260), nullable=False)
    mode: Mapped[SessionMode] = mapped_column(
        enum_column(SessionMode), nullable=False, index=True
    )
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    set_id: Mapped[int | None] = mapped_column(
        ForeignKey("question_sets.id", ondelete="SET NULL"), nullable=True
    )
    feedback_mode: Mapped[FeedbackMode] = mapped_column(
        enum_column(FeedbackMode), default=FeedbackMode.immediate, nullable=False
    )
    per_question_limit_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        enum_column(SessionStatus),
        default=SessionStatus.in_progress,
        nullable=False,
        index=True,
    )
    total_planned: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    topic: Mapped[Topic | None] = relationship()
    question_set: Mapped[QuestionSet | None] = relationship()
    items: Mapped[list[SessionItem]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionItem.position",
    )
    attempts: Mapped[list[Attempt]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Attempt.id",
    )


class SessionItem(Base):
    __tablename__ = "session_items"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="uq_session_item_position"),
        UniqueConstraint("session_id", "question_id", name="uq_session_item_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    shown_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session: Mapped[QuizSession] = relationship(back_populates="items")
    question: Mapped[Question] = relationship()


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_attempt_session_question"),
        Index("ix_attempts_answered_on", "answered_on"),
        Index("ix_attempts_question_answered", "question_id", "answered_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    selected_alternative_id: Mapped[int | None] = mapped_column(
        ForeignKey("alternatives.id", ondelete="SET NULL"), nullable=True
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timed_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    answered_on: Mapped[date] = mapped_column(Date, default=local_today, nullable=False)

    session: Mapped[QuizSession] = relationship(back_populates="attempts")
    question: Mapped[Question] = relationship()
    selected_alternative: Mapped[Alternative | None] = relationship()
