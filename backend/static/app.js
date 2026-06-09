document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('text-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const btnText = analyzeBtn.querySelector('.btn-text');
    const loader = analyzeBtn.querySelector('.loader');
    
    const resultPanel = document.getElementById('result-panel');
    const karScoreEl = document.getElementById('k-ar-score');
    const summaryEl = document.getElementById('score-summary');
    const statSentences = document.getElementById('stat-sentences');
    const statWords = document.getElementById('stat-words');
    const statAvgLen = document.getElementById('stat-avg-len');
    const statComplexRatio = document.getElementById('stat-complex-ratio');
    
    const circle = document.querySelector('.progress-ring__circle');
    const radius = circle.r.baseVal.value;
    const circumference = radius * 2 * Math.PI;
    
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference;
    
    function setProgress(percent) {
        const offset = circumference - percent / 100 * circumference;
        circle.style.strokeDashoffset = offset;
    }

    analyzeBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        if (!text) {
            alert("텍스트를 입력해주세요.");
            textInput.focus();
            return;
        }

        // Show loading state
        analyzeBtn.disabled = true;
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        resultPanel.classList.add('hidden');
        circle.style.strokeDashoffset = circumference;

        try {
            // Adjust URL for development vs production
            const apiUrl = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1') 
                ? '/api/analyze' 
                : '/api/analyze'; // Relative path works if served from FastAPI
                
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error('API request failed');
            }

            const data = await response.json();
            
            // Populate data
            karScoreEl.textContent = data.k_ar_level.toFixed(1);
            summaryEl.textContent = data.summary;
            statSentences.textContent = data.sentence_count;
            statWords.textContent = data.word_count;
            statAvgLen.textContent = data.avg_sentence_length;
            statComplexRatio.textContent = (data.complex_word_ratio * 100).toFixed(1) + '%';
            
            // Show result
            resultPanel.classList.remove('hidden');
            
            // Animate progress ring (Level 1-12 mapped to 0-100%)
            // e.g. Level 12 = 100%, Level 6 = 50%
            setTimeout(() => {
                const percent = Math.min((data.k_ar_level / 12.0) * 100, 100);
                setProgress(percent);
            }, 100);
            
            // Scroll to result
            setTimeout(() => {
                resultPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 200);

        } catch (error) {
            console.error('Error analyzing text:', error);
            alert("분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
        } finally {
            // Hide loading state
            analyzeBtn.disabled = false;
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });
});
