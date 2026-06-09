from sqlalchemy import select
from sqlalchemy.orm import Session

from models.passage import LevelBenchmark

TOPIK_MIN = 1.0
TOPIK_MAX = 6.0


def clamp_topik(level: float) -> float:
    return max(TOPIK_MIN, min(TOPIK_MAX, round(level, 1)))


def initial_topik_level(
    korean_study_months: int | None,
    self_assessed_topik: float | None,
) -> float:
    if self_assessed_topik is not None:
        return clamp_topik(self_assessed_topik)

    months = korean_study_months if korean_study_months is not None else 0
    if months <= 2:
        return 1.5
    if months <= 5:
        return 2.0
    if months <= 11:
        return 2.5
    if months <= 23:
        return 3.0
    return 3.5


def adjust_topik_after_round(current_level: float, accuracy: float) -> float:
    if accuracy >= 0.8:
        delta = 1.0
    elif accuracy >= 0.6:
        delta = 0.5
    elif accuracy >= 0.4:
        delta = 0.0
    elif accuracy >= 0.2:
        delta = -0.5
    else:
        delta = -1.0
    return clamp_topik(current_level + delta)


def get_benchmark(db: Session, topik_level: float) -> LevelBenchmark | None:
    benchmarks = db.scalars(select(LevelBenchmark)).all()
    if not benchmarks:
        return None
    return min(benchmarks, key=lambda b: abs(b.topik_level - topik_level))


def cefr_for_topik(db: Session, topik_level: float) -> str:
    benchmark = get_benchmark(db, topik_level)
    return benchmark.cefr_level if benchmark else "B1"


def summarize_result(db: Session, topik_level: float) -> tuple[str, str]:
    benchmark = get_benchmark(db, topik_level)
    if not benchmark:
        ko = f"독해 실력이 TOPIK {topik_level} 수준으로 추정됩니다."
        en = f"Your estimated reading level is TOPIK {topik_level}."
        return ko, en
    ko = f"독해 실력이 {benchmark.label_ko}({benchmark.cefr_level}) 수준입니다. {benchmark.summary_ko or ''}".strip()
    en = f"Your reading level is {benchmark.label_en} ({benchmark.cefr_level}). {benchmark.summary_en or ''}".strip()
    return ko, en
