document.addEventListener('DOMContentLoaded', () => {
    const state = {
        sessionId: null,
        maxRounds: 6,
        roundNumber: 1,
        currentLevel: 2.5,
        passage: null,
        questions: [],
        questionIndex: 0,
        selectedChoiceId: null,
        submitting: false,
    };

    const screens = {
        intro: document.getElementById('screen-intro'),
        reading: document.getElementById('screen-reading'),
        question: document.getElementById('screen-question'),
        transition: document.getElementById('screen-transition'),
        result: document.getElementById('screen-result'),
    };

    const testProgress = document.getElementById('test-progress');
    const progressLabel = document.getElementById('progress-label');
    const progressFill = document.getElementById('progress-fill');
    const homeLink = document.getElementById('home-link');

    const startBtn = document.getElementById('start-btn');
    const toQuestionsBtn = document.getElementById('to-questions-btn');
    const submitAnswerBtn = document.getElementById('submit-answer-btn');
    const choicesContainer = document.getElementById('choices-container');

    const QUESTION_TYPE_LABELS = {
        topic_identification: 'Topic',
        content_match: 'Match',
        content_mismatch: 'Mismatch',
        sequencing: 'Order',
        fill_blank: 'Blank',
        main_idea: 'Main idea',
        detail: 'Detail',
        inference: 'Inference',
        vocabulary_context: 'Vocabulary',
        practical_info: 'Practical',
    };

    function showScreen(name) {
        Object.entries(screens).forEach(([key, el]) => {
            el.classList.toggle('hidden', key !== name);
        });
        const inTest = name !== 'intro' && name !== 'result';
        testProgress.classList.toggle('hidden', !inTest);
        homeLink.classList.toggle('hidden', inTest);
    }

    function updateProgress() {
        const qTotal = state.questions.length || 5;
        const roundPart = (state.roundNumber - 1) / state.maxRounds;
        const questionPart = state.questionIndex / qTotal / state.maxRounds;
        const pct = Math.min(100, (roundPart + questionPart) * 100);
        progressLabel.textContent = `Round ${state.roundNumber} / ${state.maxRounds}`;
        progressFill.style.width = `${pct}%`;
    }

    function setLoading(btn, loading) {
        const text = btn.querySelector('.btn-text');
        const loader = btn.querySelector('.loader');
        btn.disabled = loading;
        if (text) text.classList.toggle('hidden', loading);
        if (loader) loader.classList.toggle('hidden', !loading);
    }

    async function api(path, options = {}) {
        const response = await fetch(path, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Request failed');
        }
        return response.json();
    }

    function renderPassage(passage) {
        document.getElementById('reading-round-badge').textContent = `Round ${state.roundNumber}`;
        document.getElementById('reading-level-badge').textContent = `TOPIK ~${passage.target_topik_level}`;
        document.getElementById('passage-title').textContent = passage.title;
        const titleEn = document.getElementById('passage-title-en');
        if (passage.title_en) {
            titleEn.textContent = passage.title_en;
            titleEn.classList.remove('hidden');
        } else {
            titleEn.classList.add('hidden');
        }
        document.getElementById('passage-content').textContent = passage.content;
    }

    function renderQuestion() {
        const q = state.questions[state.questionIndex];
        if (!q) return;

        state.selectedChoiceId = null;
        submitAnswerBtn.disabled = true;

        document.getElementById('question-index-badge').textContent =
            `Question ${state.questionIndex + 1} / ${state.questions.length}`;
        document.getElementById('question-type-badge').textContent =
            QUESTION_TYPE_LABELS[q.type] || q.type;

        document.getElementById('question-stem').textContent = q.stem;
        const stemEn = document.getElementById('question-stem-en');
        if (q.stem_en) {
            stemEn.textContent = q.stem_en;
            stemEn.classList.remove('hidden');
        } else {
            stemEn.classList.add('hidden');
        }

        choicesContainer.innerHTML = '';
        q.choices.forEach((choice) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'choice-btn';
            btn.dataset.choiceId = String(choice.id);
            btn.innerHTML = `<span class="choice-btn__label">${choice.label}</span><span class="choice-btn__text">${escapeHtml(choice.text)}</span>`;
            btn.addEventListener('click', () => selectChoice(choice.id, btn));
            choicesContainer.appendChild(btn);
        });

        updateProgress();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function selectChoice(choiceId, btnEl) {
        state.selectedChoiceId = choiceId;
        submitAnswerBtn.disabled = false;
        choicesContainer.querySelectorAll('.choice-btn').forEach((el) => {
            el.classList.toggle('choice-btn--selected', el === btnEl);
        });
    }

    function beginRound(data) {
        state.sessionId = data.session_id;
        state.maxRounds = data.max_rounds;
        state.roundNumber = data.round_number;
        state.currentLevel = data.current_topik_level;
        state.passage = data.passage;
        state.questions = data.questions;
        state.questionIndex = 0;
        renderPassage(state.passage);
        showScreen('reading');
        updateProgress();
    }

    function renderResult(result) {
        const topik = result.final_topik_level;
        document.getElementById('final-topik').textContent = topik.toFixed(1);
        document.getElementById('final-cefr').textContent = result.final_cefr_level;
        document.getElementById('result-summary').textContent = result.summary_en || result.summary_ko;
        document.getElementById('stat-rounds').textContent = result.total_rounds;
        document.getElementById('stat-accuracy').textContent = `${Math.round(result.overall_accuracy * 100)}%`;
        document.getElementById('stat-cefr').textContent = result.final_cefr_level;

        const tbody = document.getElementById('round-table-body');
        tbody.innerHTML = '';
        result.rounds.forEach((round) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${round.round_number}</td>
                <td>${escapeHtml(round.passage_title)}</td>
                <td>${round.correct_count}/${round.total_count}</td>
                <td>TOPIK ${round.topik_level_after.toFixed(1)}</td>
            `;
            tbody.appendChild(tr);
        });

        const circle = document.querySelector('.progress-ring__circle--result');
        if (circle) {
            const radius = circle.r.baseVal.value;
            const circumference = radius * 2 * Math.PI;
            circle.style.strokeDasharray = `${circumference} ${circumference}`;
            const pct = Math.min((topik / 6) * 100, 100);
            setTimeout(() => {
                circle.style.strokeDashoffset = circumference - (pct / 100) * circumference;
            }, 150);
        }

        showScreen('result');
    }

    async function handleRoundEnd(resp) {
        if (resp.test_completed && resp.result) {
            renderResult(resp.result);
            return;
        }

        if (resp.next_passage && resp.next_questions) {
            showScreen('transition');
            const summary = resp.round_summary;
            if (summary) {
                document.getElementById('transition-text').textContent =
                    `Round ${summary.round_number}: ${summary.correct_count}/${summary.total_count} correct. ` +
                    `Level ${summary.topik_level_before} → ${summary.topik_level_after}`;
            }

            await new Promise((r) => setTimeout(r, 1200));

            state.roundNumber += 1;
            state.currentLevel = resp.round_summary?.topik_level_after ?? state.currentLevel;
            state.passage = resp.next_passage;
            state.questions = resp.next_questions;
            state.questionIndex = 0;
            renderPassage(state.passage);
            showScreen('reading');
            updateProgress();
            return;
        }

        const result = await api(`/api/test/sessions/${state.sessionId}/result`);
        renderResult(result);
    }

    startBtn.addEventListener('click', async () => {
        const months = parseInt(document.getElementById('input-months').value, 10);
        const topikVal = document.getElementById('input-topik').value;
        const payload = {
            display_name: document.getElementById('input-name').value.trim() || null,
            native_language: document.getElementById('input-lang').value,
            ui_locale: 'en',
            korean_study_months: months,
            self_assessed_topik: topikVal ? parseFloat(topikVal) : null,
        };

        setLoading(startBtn, true);
        try {
            const data = await api('/api/test/sessions', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            beginRound(data);
        } catch (error) {
            console.error(error);
            alert('Could not start the test. Make sure the server is running and seed data is loaded.');
        } finally {
            setLoading(startBtn, false);
        }
    });

    toQuestionsBtn.addEventListener('click', () => {
        renderQuestion();
        showScreen('question');
    });

    submitAnswerBtn.addEventListener('click', async () => {
        if (!state.selectedChoiceId || state.submitting) return;
        const question = state.questions[state.questionIndex];
        state.submitting = true;
        setLoading(submitAnswerBtn, true);

        try {
            const resp = await api(`/api/test/sessions/${state.sessionId}/answers`, {
                method: 'POST',
                body: JSON.stringify({
                    question_id: question.id,
                    choice_id: state.selectedChoiceId,
                }),
            });

            if (resp.is_last_question_in_round) {
                await handleRoundEnd(resp);
            } else {
                state.questionIndex += 1;
                renderQuestion();
            }
        } catch (error) {
            console.error(error);
            alert('Failed to submit answer. Please try again.');
        } finally {
            state.submitting = false;
            setLoading(submitAnswerBtn, false);
        }
    });
});
