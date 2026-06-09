-- K-Reading Index: foreign learner (KSL) schema

CREATE TABLE IF NOT EXISTS level_benchmarks (
    topik_level         REAL PRIMARY KEY,
    cefr_level          TEXT NOT NULL,
    label_ko            TEXT NOT NULL,
    label_en            TEXT NOT NULL,
    vocab_size_hint     INTEGER,
    study_months_hint   TEXT,
    summary_ko          TEXT,
    summary_en          TEXT,
    passage_char_min    INTEGER,
    passage_char_max    INTEGER
);

CREATE TABLE IF NOT EXISTS question_types (
    code                TEXT PRIMARY KEY,
    label_ko            TEXT NOT NULL,
    label_en            TEXT NOT NULL,
    topik_section       TEXT,
    difficulty_weight   REAL NOT NULL DEFAULT 1.0,
    sort_order          INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS passages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    title               TEXT NOT NULL,
    title_en            TEXT,
    content             TEXT NOT NULL,
    content_plain       TEXT,
    target_topik_level  REAL NOT NULL,
    cefr_level          TEXT,
    topic_category      TEXT NOT NULL DEFAULT 'daily_life',
    grammar_tags        TEXT,
    key_vocab           TEXT,
    char_count          INTEGER NOT NULL DEFAULT 0,
    word_count          INTEGER NOT NULL DEFAULT 0,
    sentence_count      INTEGER NOT NULL DEFAULT 0,
    estimated_read_time_sec INTEGER,
    analyzer_avg_sentence_len REAL,
    analyzer_complex_word_ratio REAL,
    source_type         TEXT NOT NULL DEFAULT 'original',
    source_name         TEXT,
    source_url          TEXT,
    license_type        TEXT,
    commercial_ok       INTEGER NOT NULL DEFAULT 0,
    derivative_ok       INTEGER NOT NULL DEFAULT 1,
    learner_type        TEXT NOT NULL DEFAULT 'ksl',
    is_active           INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (target_topik_level BETWEEN 1.0 AND 6.0),
    CHECK (learner_type IN ('ksl', 'native'))
);

CREATE INDEX IF NOT EXISTS idx_passages_topik ON passages(target_topik_level);
CREATE INDEX IF NOT EXISTS idx_passages_topic ON passages(topic_category);
CREATE INDEX IF NOT EXISTS idx_passages_active ON passages(is_active, learner_type);

CREATE TABLE IF NOT EXISTS questions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id          INTEGER NOT NULL REFERENCES passages(id) ON DELETE CASCADE,
    question_type       TEXT NOT NULL REFERENCES question_types(code),
    order_index         INTEGER NOT NULL,
    stem                TEXT NOT NULL,
    stem_en             TEXT,
    explanation         TEXT,
    explanation_en      TEXT,
    meta                TEXT,
    points              INTEGER NOT NULL DEFAULT 1,
    is_active           INTEGER NOT NULL DEFAULT 1,
    UNIQUE(passage_id, order_index)
);

CREATE INDEX IF NOT EXISTS idx_questions_passage ON questions(passage_id);
CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type);

CREATE TABLE IF NOT EXISTS choices (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id         INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    label               TEXT NOT NULL,
    text                TEXT NOT NULL,
    text_en             TEXT,
    is_correct          INTEGER NOT NULL DEFAULT 0,
    UNIQUE(question_id, label)
);

CREATE INDEX IF NOT EXISTS idx_choices_question ON choices(question_id);

CREATE TABLE IF NOT EXISTS test_sessions (
    id                  TEXT PRIMARY KEY,
    display_name        TEXT,
    native_language     TEXT NOT NULL DEFAULT 'en',
    ui_locale           TEXT NOT NULL DEFAULT 'en',
    korean_study_months INTEGER,
    self_assessed_topik REAL,
    status              TEXT NOT NULL DEFAULT 'in_progress',
    current_topik_level REAL NOT NULL,
    final_topik_level   REAL,
    final_cefr_level    TEXT,
    max_rounds          INTEGER NOT NULL DEFAULT 6,
    completed_rounds    INTEGER NOT NULL DEFAULT 0,
    total_correct       INTEGER NOT NULL DEFAULT 0,
    total_answered      INTEGER NOT NULL DEFAULT 0,
    overall_accuracy    REAL,
    result_summary_ko   TEXT,
    result_summary_en   TEXT,
    learner_type        TEXT NOT NULL DEFAULT 'ksl',
    started_at          TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at        TEXT,
    CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    CHECK (current_topik_level BETWEEN 1.0 AND 6.0)
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON test_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON test_sessions(started_at);

CREATE TABLE IF NOT EXISTS test_rounds (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    round_number        INTEGER NOT NULL,
    passage_id          INTEGER NOT NULL REFERENCES passages(id),
    topik_level_at_start REAL NOT NULL,
    topik_level_at_end   REAL,
    correct_count       INTEGER,
    total_count         INTEGER NOT NULL DEFAULT 5,
    accuracy            REAL,
    started_at          TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at        TEXT,
    UNIQUE(session_id, round_number)
);

CREATE INDEX IF NOT EXISTS idx_rounds_session ON test_rounds(session_id);

CREATE TABLE IF NOT EXISTS test_answers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id            INTEGER NOT NULL REFERENCES test_rounds(id) ON DELETE CASCADE,
    question_id         INTEGER NOT NULL REFERENCES questions(id),
    selected_choice_id  INTEGER NOT NULL REFERENCES choices(id),
    is_correct          INTEGER NOT NULL,
    question_type       TEXT NOT NULL,
    answered_at         TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(round_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_answers_round ON test_answers(round_id);

CREATE VIEW IF NOT EXISTS session_used_passages AS
SELECT session_id, passage_id
FROM test_rounds;
