import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from models.passage import Question
from models.test_session import TestAnswer, TestRound, TestSession
from schemas.test import (
    AnswerResponse,
    PassageOut,
    QuestionOut,
    RoundResultOut,
    RoundSummary,
    SessionStatusResponse,
    StartSessionResponse,
    TestResultOut,
)
from services.level_resolver import (
    adjust_topik_after_round,
    cefr_for_topik,
    clamp_topik,
    initial_topik_level,
    summarize_result,
)
from services.passage_service import (
    get_passage_with_questions,
    get_used_passage_ids,
    passage_to_out,
    question_to_out,
    select_passage_for_level,
)


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _questions_for_round(passage) -> list[QuestionOut]:
    active = [q for q in passage.questions if q.is_active]
    active.sort(key=lambda q: q.order_index)
    return [question_to_out(q) for q in active[:5]]


def _get_current_round(db: Session, session: TestSession) -> TestRound | None:
    return db.scalar(
        select(TestRound)
        .options(
            selectinload(TestRound.answers),
        )
        .where(
            TestRound.session_id == session.id,
            TestRound.round_number == session.completed_rounds + 1,
            TestRound.completed_at.is_(None),
        )
    )


def _should_complete_test(session: TestSession, recent_accuracies: list[float]) -> bool:
    if session.completed_rounds + 1 >= session.max_rounds:
        return True
    if len(recent_accuracies) >= 2:
        last_two = recent_accuracies[-2:]
        if all(0.4 <= a < 0.8 for a in last_two):
            return True
    return False


def _compute_final_level(rounds: list[TestRound], fallback: float) -> float:
    if not rounds:
        return fallback
    if len(rounds) == 1:
        return rounds[-1].topik_level_at_end or fallback
    end_levels = [r.topik_level_at_end for r in rounds[-2:] if r.topik_level_at_end is not None]
    if not end_levels:
        return fallback
    return clamp_topik(sum(end_levels) / len(end_levels))


def _build_result(db: Session, session: TestSession) -> TestResultOut:
    rounds = db.scalars(
        select(TestRound)
        .where(TestRound.session_id == session.id, TestRound.completed_at.is_not(None))
        .order_by(TestRound.round_number)
    ).all()

    final_level = session.final_topik_level or _compute_final_level(
        rounds, session.current_topik_level
    )
    cefr = session.final_cefr_level or cefr_for_topik(db, final_level)
    summary_ko, summary_en = (
        (session.result_summary_ko, session.result_summary_en)
        if session.result_summary_ko and session.result_summary_en
        else summarize_result(db, final_level)
    )

    total_correct = sum(r.correct_count or 0 for r in rounds)
    total_count = sum(r.total_count or 0 for r in rounds)
    overall_accuracy = session.overall_accuracy
    if overall_accuracy is None:
        overall_accuracy = total_correct / total_count if total_count else 0.0

    round_results = []
    for r in rounds:
        passage = get_passage_with_questions(db, r.passage_id)
        round_results.append(
            RoundResultOut(
                round_number=r.round_number,
                passage_title=passage.title if passage else "",
                target_topik_level=passage.target_topik_level if passage else 0,
                correct_count=r.correct_count or 0,
                total_count=r.total_count or 0,
                topik_level_after=r.topik_level_at_end or session.current_topik_level,
            )
        )

    return TestResultOut(
        final_topik_level=final_level,
        final_cefr_level=cefr,
        summary_ko=summary_ko,
        summary_en=summary_en,
        rounds=round_results,
        overall_accuracy=round(overall_accuracy, 3),
        total_rounds=len(rounds),
    )


def _finalize_session(db: Session, session: TestSession) -> TestResultOut:
    rounds = db.scalars(
        select(TestRound)
        .where(TestRound.session_id == session.id, TestRound.completed_at.is_not(None))
        .order_by(TestRound.round_number)
    ).all()

    final_level = _compute_final_level(rounds, session.current_topik_level)
    cefr = cefr_for_topik(db, final_level)
    summary_ko, summary_en = summarize_result(db, final_level)

    total_correct = sum(r.correct_count or 0 for r in rounds)
    total_count = sum(r.total_count or 0 for r in rounds)
    overall_accuracy = total_correct / total_count if total_count else 0.0

    session.status = "completed"
    session.final_topik_level = final_level
    session.final_cefr_level = cefr
    session.result_summary_ko = summary_ko
    session.result_summary_en = summary_en
    session.overall_accuracy = round(overall_accuracy, 3)
    session.completed_at = _now()
    db.commit()
    return _build_result(db, session)


def start_session(db: Session, payload) -> StartSessionResponse:
    start_level = initial_topik_level(
        payload.korean_study_months,
        payload.self_assessed_topik,
    )
    passage = select_passage_for_level(db, start_level, set())
    if not passage:
        raise HTTPException(
            status_code=503,
            detail="No passages available. Import seed data first.",
        )

    session_id = str(uuid.uuid4())
    now = _now()
    session = TestSession(
        id=session_id,
        display_name=payload.display_name,
        native_language=payload.native_language,
        ui_locale=payload.ui_locale,
        korean_study_months=payload.korean_study_months,
        self_assessed_topik=payload.self_assessed_topik,
        status="in_progress",
        current_topik_level=start_level,
        max_rounds=6,
        completed_rounds=0,
        learner_type="ksl",
        started_at=now,
    )
    db.add(session)
    db.flush()

    db.add(
        TestRound(
            session_id=session_id,
            round_number=1,
            passage_id=passage.id,
            topik_level_at_start=start_level,
            total_count=5,
            started_at=now,
        )
    )
    db.commit()

    questions = _questions_for_round(passage)
    return StartSessionResponse(
        session_id=session_id,
        status="in_progress",
        current_topik_level=start_level,
        round_number=1,
        max_rounds=session.max_rounds,
        passage=passage_to_out(passage),
        questions=questions,
        total_questions_in_round=len(questions),
    )


def get_session_status(db: Session, session_id: str) -> SessionStatusResponse:
    session = db.get(TestSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current_round = _get_current_round(db, session)
    answered = 0
    total = 5
    if current_round:
        answered = len(current_round.answers)
        total = current_round.total_count

    return SessionStatusResponse(
        session_id=session.id,
        status=session.status,
        current_topik_level=session.current_topik_level,
        round_number=session.completed_rounds + (0 if session.status == "completed" else 1),
        max_rounds=session.max_rounds,
        answered_in_current_round=answered,
        total_questions_in_round=total,
        completed_rounds=session.completed_rounds,
    )


def submit_answer(db: Session, session_id: str, question_id: int, choice_id: int) -> AnswerResponse:
    session = db.get(TestSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Session already completed")

    current_round = _get_current_round(db, session)
    if not current_round:
        raise HTTPException(status_code=400, detail="No active round")

    question = db.scalar(
        select(Question)
        .options(selectinload(Question.choices))
        .where(Question.id == question_id, Question.passage_id == current_round.passage_id)
    )
    if not question:
        raise HTTPException(status_code=400, detail="Invalid question for current round")

    existing = db.scalar(
        select(TestAnswer).where(
            TestAnswer.round_id == current_round.id,
            TestAnswer.question_id == question_id,
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Question already answered")

    choice = next((c for c in question.choices if c.id == choice_id), None)
    if not choice:
        raise HTTPException(status_code=400, detail="Invalid choice")

    is_correct = bool(choice.is_correct)
    db.add(
        TestAnswer(
            round_id=current_round.id,
            question_id=question.id,
            selected_choice_id=choice.id,
            is_correct=is_correct,
            question_type=question.question_type,
            answered_at=_now(),
        )
    )
    session.total_answered += 1
    if is_correct:
        session.total_correct += 1
    db.flush()

    answered_count = db.scalar(
        select(func.count()).select_from(TestAnswer).where(TestAnswer.round_id == current_round.id)
    ) or 0
    passage = get_passage_with_questions(db, current_round.passage_id)
    active_questions = [q for q in passage.questions if q.is_active] if passage else []
    total_questions = min(5, len(active_questions))

    if answered_count < total_questions:
        db.commit()
        return AnswerResponse(
            accepted=True,
            is_last_question_in_round=False,
            next_question_order=answered_count + 1,
        )

    # Round complete
    correct_count = db.scalar(
        select(func.count())
        .select_from(TestAnswer)
        .where(TestAnswer.round_id == current_round.id, TestAnswer.is_correct.is_(True))
    ) or 0
    accuracy = correct_count / total_questions if total_questions else 0.0
    level_before = current_round.topik_level_at_start
    level_after = adjust_topik_after_round(level_before, accuracy)

    current_round.correct_count = correct_count
    current_round.accuracy = round(accuracy, 3)
    current_round.topik_level_at_end = level_after
    current_round.completed_at = _now()
    session.current_topik_level = level_after
    session.completed_rounds += 1
    db.flush()

    round_summary = RoundSummary(
        round_number=current_round.round_number,
        correct_count=correct_count,
        total_count=total_questions,
        accuracy=round(accuracy, 3),
        topik_level_before=level_before,
        topik_level_after=level_after,
    )

    completed_rounds = db.scalars(
        select(TestRound)
        .where(TestRound.session_id == session.id, TestRound.completed_at.is_not(None))
        .order_by(TestRound.round_number)
    ).all()
    recent_accuracies = [r.accuracy or 0.0 for r in completed_rounds]

    if _should_complete_test(session, recent_accuracies):
        result = _finalize_session(db, session)
        return AnswerResponse(
            accepted=True,
            is_last_question_in_round=True,
            round_summary=round_summary,
            test_completed=True,
            result=result,
        )

    next_passage = select_passage_for_level(
        db,
        level_after,
        get_used_passage_ids(db, session.id),
    )
    if not next_passage:
        result = _finalize_session(db, session)
        return AnswerResponse(
            accepted=True,
            is_last_question_in_round=True,
            round_summary=round_summary,
            test_completed=True,
            result=result,
        )

    db.add(
        TestRound(
            session_id=session.id,
            round_number=session.completed_rounds + 1,
            passage_id=next_passage.id,
            topik_level_at_start=level_after,
            total_count=5,
            started_at=_now(),
        )
    )
    db.commit()

    next_questions = _questions_for_round(next_passage)
    return AnswerResponse(
        accepted=True,
        is_last_question_in_round=True,
        round_summary=round_summary,
        test_completed=False,
        next_passage=passage_to_out(next_passage),
        next_questions=next_questions,
    )


def get_result(db: Session, session_id: str) -> TestResultOut:
    session = db.get(TestSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Session not completed yet")
    return _build_result(db, session)
