from fastapi import APIRouter

from analyzer import analyze_text_complexity
from schemas.analyze import AnalyzeResponse, TextRequest

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: TextRequest):
    return analyze_text_complexity(request.text)
