from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class LevelBenchmark(Base):
    __tablename__ = "level_benchmarks"

    topik_level: Mapped[float] = mapped_column(Float, primary_key=True)
    cefr_level: Mapped[str] = mapped_column(String, nullable=False)
    label_ko: Mapped[str] = mapped_column(String, nullable=False)
    label_en: Mapped[str] = mapped_column(String, nullable=False)
    vocab_size_hint: Mapped[int | None] = mapped_column(Integer)
    study_months_hint: Mapped[str | None] = mapped_column(String)
    summary_ko: Mapped[str | None] = mapped_column(Text)
    summary_en: Mapped[str | None] = mapped_column(Text)
    passage_char_min: Mapped[int | None] = mapped_column(Integer)
    passage_char_max: Mapped[int | None] = mapped_column(Integer)


class QuestionType(Base):
    __tablename__ = "question_types"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    label_ko: Mapped[str] = mapped_column(String, nullable=False)
    label_en: Mapped[str] = mapped_column(String, nullable=False)
    topik_section: Mapped[str | None] = mapped_column(String)
    difficulty_weight: Mapped[float] = mapped_column(Float, default=1.0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class Passage(Base):
    __tablename__ = "passages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    title_en: Mapped[str | None] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_plain: Mapped[str | None] = mapped_column(Text)
    target_topik_level: Mapped[float] = mapped_column(Float, nullable=False)
    cefr_level: Mapped[str | None] = mapped_column(String)
    topic_category: Mapped[str] = mapped_column(String, default="daily_life")
    grammar_tags: Mapped[str | None] = mapped_column(Text)
    key_vocab: Mapped[str | None] = mapped_column(Text)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    sentence_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_read_time_sec: Mapped[int | None] = mapped_column(Integer)
    analyzer_avg_sentence_len: Mapped[float | None] = mapped_column(Float)
    analyzer_complex_word_ratio: Mapped[float | None] = mapped_column(Float)
    source_type: Mapped[str] = mapped_column(String, default="original")
    source_name: Mapped[str | None] = mapped_column(String)
    source_url: Mapped[str | None] = mapped_column(String)
    license_type: Mapped[str | None] = mapped_column(String)
    commercial_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    derivative_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    learner_type: Mapped[str] = mapped_column(String, default="ksl")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)

    questions: Mapped[list["Question"]] = relationship(back_populates="passage", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("passage_id", "order_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    passage_id: Mapped[int] = mapped_column(ForeignKey("passages.id", ondelete="CASCADE"), nullable=False)
    question_type: Mapped[str] = mapped_column(ForeignKey("question_types.code"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    stem_en: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    explanation_en: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[str | None] = mapped_column(Text)
    points: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    passage: Mapped["Passage"] = relationship(back_populates="questions")
    choices: Mapped[list["Choice"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class Choice(Base):
    __tablename__ = "choices"
    __table_args__ = (UniqueConstraint("question_id", "label"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_en: Mapped[str | None] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    question: Mapped["Question"] = relationship(back_populates="choices")
