from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import (
    AnswerSource,
    Difficulty,
    QuestionOrigin,
    QuestionType,
    ReviewStatus,
    SourceKind,
)

SINGLE_CHOICE_LABELS = set("ABCDE")


class TopicIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    slug: str = Field(min_length=1, max_length=140)
    name: str = Field(min_length=1, max_length=180)
    description: str = ""
    parent: str | None = Field(default=None, max_length=140)
    position: int = 0

    @field_validator("parent")
    @classmethod
    def empty_parent_to_none(cls, value: str | None) -> str | None:
        return value or None


class TopicCatalog(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    topics: list[TopicIn] = Field(default_factory=list)


class ExamIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    slug: str = Field(min_length=1, max_length=180)
    name: str = Field(min_length=1, max_length=220)
    organization: str = ""
    year: int | None = None
    role: str = ""
    edital: str = ""
    source_url: str | None = None
    answer_key_url: str | None = None


class ExamCatalog(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    exams: list[ExamIn] = Field(default_factory=list)


class TagIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    slug: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=180)
    area: str = Field(min_length=1, max_length=120)
    position: int = 0
    description: str = ""


class TagCatalog(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    tags: list[TagIn] = Field(default_factory=list)


class AlternativeIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    label: str = Field(min_length=1, max_length=8)
    text: str = Field(min_length=1)
    is_correct: bool = False
    explanation: str = ""
    media_url: str | None = None

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str) -> str:
        return value.strip().upper()


class QuestionIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    external_id: str = Field(min_length=1, max_length=180)
    topic: str = Field(min_length=1, max_length=140)
    exam: str | None = Field(default=None, max_length=180)
    type: QuestionType
    statement: str = Field(min_length=1)
    context: str = ""
    media_url: str | None = None
    context_media_url: str | None = None
    difficulty: Difficulty | None = None
    source: str = ""
    source_url: str | None = None
    source_question_number: str | None = None
    general_explanation: str = ""
    origin: QuestionOrigin = QuestionOrigin.authored
    answer_source: AnswerSource = AnswerSource.manual
    explanation_source: SourceKind = SourceKind.manual
    tag: str = Field(min_length=1, max_length=160)
    review_status: ReviewStatus | None = None
    alternatives: list[AlternativeIn] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_shape(self) -> QuestionIn:
        labels = [alt.label for alt in self.alternatives]
        if len(labels) != len(set(labels)):
            raise ValueError("as alternativas devem ter rótulos únicos")

        correct = sum(1 for alt in self.alternatives if alt.is_correct)
        if correct != 1:
            raise ValueError("exatamente uma alternativa deve ser correta")

        if self.type == QuestionType.true_false:
            if set(labels) != {"C", "E"}:
                raise ValueError("questões de certo/errado devem ter apenas as alternativas C e E")
        elif set(labels) - SINGLE_CHOICE_LABELS:
            raise ValueError("alternativas de múltipla escolha devem usar os rótulos A a E")
        return self

    @field_validator("exam")
    @classmethod
    def empty_exam_to_none(cls, value: str | None) -> str | None:
        return value or None


class QuestionFile(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    topics: list[TopicIn] = Field(default_factory=list)
    exams: list[ExamIn] = Field(default_factory=list)
    questions: list[QuestionIn] = Field(default_factory=list)


class MaterialMeta(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=220)
    slug: str | None = Field(default=None, max_length=180)
    summary: str = ""
    topics: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: str = ""
    source_url: str | None = None
    source_kind: SourceKind = SourceKind.manual
    review_status: ReviewStatus = ReviewStatus.approved
