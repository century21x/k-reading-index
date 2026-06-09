import json
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models.passage import Choice, Passage, Question
from models.test_session import TestRound
from schemas.test import ChoiceOut, PassageOut, QuestionOut


def _plain_text(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip()


def passage_to_out(passage: Passage) -> PassageOut:
    return PassageOut(
        id=passage.id,
        title=passage.title,
        title_en=passage.title_en,
        content=passage.content,
        target_topik_level=passage.target_topik_level,
        cefr_level=passage.cefr_level,
        word_count=passage.word_count,
    )


def question_to_out(question: Question) -> QuestionOut:
    return QuestionOut(
        id=question.id,
        order=question.order_index,
        type=question.question_type,
        stem=question.stem,
        stem_en=question.stem_en,
        choices=[
            ChoiceOut(id=c.id, label=c.label, text=c.text, text_en=c.text_en)
            for c in sorted(question.choices, key=lambda x: x.label)
        ],
    )


def get_passage_with_questions(db: Session, passage_id: int) -> Passage | None:
    return db.scalar(
        select(Passage)
        .options(selectinload(Passage.questions).selectinload(Question.choices))
        .where(Passage.id == passage_id, Passage.is_active.is_(True))
    )


def get_used_passage_ids(db: Session, session_id: str) -> set[int]:
    rows = db.scalars(
        select(TestRound.passage_id).where(TestRound.session_id == session_id)
    ).all()
    return set(rows)


def select_passage_for_level(
    db: Session,
    target_level: float,
    exclude_ids: set[int],
) -> Passage | None:
    stmt = (
        select(Passage)
        .options(selectinload(Passage.questions).selectinload(Question.choices))
        .where(Passage.is_active.is_(True), Passage.learner_type == "ksl")
    )
    if exclude_ids:
        stmt = stmt.where(Passage.id.not_in(exclude_ids))
    passages = db.scalars(stmt).all()
    passages = [p for p in passages if len(p.questions) >= 5]
    if not passages:
        return None
    return min(passages, key=lambda p: abs(p.target_topik_level - target_level))


def create_passage_from_dict(db: Session, data: dict, analyzer_fn=None) -> Passage:
    content = data["content"]
    plain = _plain_text(content)
    char_count = len(plain)
    topik = float(data["target_topik_level"])

    analyzer_avg = None
    analyzer_ratio = None
    sentence_count = 0
    word_count = 0
    if analyzer_fn:
        result = analyzer_fn(content)
        analyzer_avg = result.get("avg_sentence_length")
        analyzer_ratio = result.get("complex_word_ratio")
        sentence_count = result.get("sentence_count", 0)
        word_count = result.get("word_count", 0)

    now = datetime.utcnow().isoformat(timespec="seconds")
    passage = Passage(
        title=data["title"],
        title_en=data.get("title_en"),
        content=content,
        content_plain=plain,
        target_topik_level=topik,
        cefr_level=data.get("cefr_level"),
        topic_category=data.get("topic_category", "daily_life"),
        grammar_tags=json.dumps(data.get("grammar_tags", []), ensure_ascii=False) if data.get("grammar_tags") else None,
        key_vocab=json.dumps(data.get("key_vocab", []), ensure_ascii=False) if data.get("key_vocab") else None,
        char_count=char_count,
        word_count=word_count or len(plain.split()),
        sentence_count=sentence_count,
        estimated_read_time_sec=max(30, char_count // 5),
        analyzer_avg_sentence_len=analyzer_avg,
        analyzer_complex_word_ratio=analyzer_ratio,
        source_type=data.get("source_type", "original"),
        source_name=data.get("source_name"),
        source_url=data.get("source_url"),
        license_type=data.get("license_type", "original"),
        commercial_ok=bool(data.get("commercial_ok", False)),
        derivative_ok=bool(data.get("derivative_ok", True)),
        learner_type=data.get("learner_type", "ksl"),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(passage)
    db.flush()

    for q in data.get("questions", []):
        question = Question(
            passage_id=passage.id,
            question_type=q["question_type"],
            order_index=q["order_index"],
            stem=q["stem"],
            stem_en=q.get("stem_en"),
            explanation=q.get("explanation"),
            explanation_en=q.get("explanation_en"),
            meta=json.dumps(q["meta"], ensure_ascii=False) if q.get("meta") else None,
            points=q.get("points", 1),
            is_active=True,
        )
        db.add(question)
        db.flush()
        for choice in q.get("choices", []):
            db.add(
                Choice(
                    question_id=question.id,
                    label=choice["label"],
                    text=choice["text"],
                    text_en=choice.get("text_en"),
                    is_correct=bool(choice.get("is_correct", False)),
                )
            )
    db.flush()
    return passage
