from pydantic import BaseModel, Field


class ChoiceOut(BaseModel):
    id: int
    label: str
    text: str
    text_en: str | None = None

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: int
    order: int
    type: str
    stem: str
    stem_en: str | None = None
    choices: list[ChoiceOut]

    model_config = {"from_attributes": True}


class PassageOut(BaseModel):
    id: int
    title: str
    title_en: str | None = None
    content: str
    target_topik_level: float
    cefr_level: str | None = None
    word_count: int = 0

    model_config = {"from_attributes": True}


class StartSessionRequest(BaseModel):
    display_name: str | None = None
    native_language: str = "en"
    ui_locale: str = "en"
    korean_study_months: int | None = None
    self_assessed_topik: float | None = Field(default=None, ge=1.0, le=6.0)


class StartSessionResponse(BaseModel):
    session_id: str
    status: str
    current_topik_level: float
    round_number: int
    max_rounds: int
    passage: PassageOut
    questions: list[QuestionOut]
    total_questions_in_round: int


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    current_topik_level: float
    round_number: int
    max_rounds: int
    answered_in_current_round: int
    total_questions_in_round: int
    completed_rounds: int


class AnswerRequest(BaseModel):
    question_id: int
    choice_id: int


class RoundSummary(BaseModel):
    round_number: int
    correct_count: int
    total_count: int
    accuracy: float
    topik_level_before: float
    topik_level_after: float


class RoundResultOut(BaseModel):
    round_number: int
    passage_title: str
    target_topik_level: float
    correct_count: int
    total_count: int
    topik_level_after: float


class TestResultOut(BaseModel):
    final_topik_level: float
    final_cefr_level: str
    summary_ko: str
    summary_en: str
    rounds: list[RoundResultOut]
    overall_accuracy: float
    total_rounds: int


class AnswerResponse(BaseModel):
    accepted: bool
    is_last_question_in_round: bool
    next_question_order: int | None = None
    round_summary: RoundSummary | None = None
    test_completed: bool = False
    next_passage: PassageOut | None = None
    next_questions: list[QuestionOut] | None = None
    result: TestResultOut | None = None
