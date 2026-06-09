from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.test import (
    AnswerRequest,
    AnswerResponse,
    SessionStatusResponse,
    StartSessionRequest,
    StartSessionResponse,
    TestResultOut,
)
from services import topik_engine

router = APIRouter(prefix="/api/test", tags=["test"])


@router.post("/sessions", response_model=StartSessionResponse, status_code=201)
def create_session(payload: StartSessionRequest, db: Session = Depends(get_db)):
    return topik_engine.start_session(db, payload)


@router.get("/sessions/{session_id}", response_model=SessionStatusResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    return topik_engine.get_session_status(db, session_id)


@router.post("/sessions/{session_id}/answers", response_model=AnswerResponse)
def submit_answer(
    session_id: str,
    payload: AnswerRequest,
    db: Session = Depends(get_db),
):
    return topik_engine.submit_answer(db, session_id, payload.question_id, payload.choice_id)


@router.get("/sessions/{session_id}/result", response_model=TestResultOut)
def get_result(session_id: str, db: Session = Depends(get_db)):
    return topik_engine.get_result(db, session_id)
