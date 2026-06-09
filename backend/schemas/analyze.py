from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    text: str = Field(min_length=1)


class AnalyzeResponse(BaseModel):
    k_ar_level: float
    sentence_count: int
    word_count: int
    avg_sentence_length: float
    complex_word_ratio: float
    summary: str
