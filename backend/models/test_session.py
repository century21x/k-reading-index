from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class TestSession(Base):
    __tablename__ = "test_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String)
    native_language: Mapped[str] = mapped_column(String, default="en")
    ui_locale: Mapped[str] = mapped_column(String, default="en")
    korean_study_months: Mapped[int | None] = mapped_column(Integer)
    self_assessed_topik: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="in_progress")
    current_topik_level: Mapped[float] = mapped_column(Float, nullable=False)
    final_topik_level: Mapped[float | None] = mapped_column(Float)
    final_cefr_level: Mapped[str | None] = mapped_column(String)
    max_rounds: Mapped[int] = mapped_column(Integer, default=6)
    completed_rounds: Mapped[int] = mapped_column(Integer, default=0)
    total_correct: Mapped[int] = mapped_column(Integer, default=0)
    total_answered: Mapped[int] = mapped_column(Integer, default=0)
    overall_accuracy: Mapped[float | None] = mapped_column(Float)
    result_summary_ko: Mapped[str | None] = mapped_column(Text)
    result_summary_en: Mapped[str | None] = mapped_column(Text)
    learner_type: Mapped[str] = mapped_column(String, default="ksl")
    started_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String)

    rounds: Mapped[list["TestRound"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class TestRound(Base):
    __tablename__ = "test_rounds"
    __table_args__ = (UniqueConstraint("session_id", "round_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    passage_id: Mapped[int] = mapped_column(ForeignKey("passages.id"), nullable=False)
    topik_level_at_start: Mapped[float] = mapped_column(Float, nullable=False)
    topik_level_at_end: Mapped[float | None] = mapped_column(Float)
    correct_count: Mapped[int | None] = mapped_column(Integer)
    total_count: Mapped[int] = mapped_column(Integer, default=5)
    accuracy: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String)

    session: Mapped["TestSession"] = relationship(back_populates="rounds")
    answers: Mapped[list["TestAnswer"]] = relationship(back_populates="round", cascade="all, delete-orphan")


class TestAnswer(Base):
    __tablename__ = "test_answers"
    __table_args__ = (UniqueConstraint("round_id", "question_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("test_rounds.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    selected_choice_id: Mapped[int] = mapped_column(ForeignKey("choices.id"), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    question_type: Mapped[str] = mapped_column(String, nullable=False)
    answered_at: Mapped[str] = mapped_column(String)

    round: Mapped["TestRound"] = relationship(back_populates="answers")
