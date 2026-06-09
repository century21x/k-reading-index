from kiwipiepy import Kiwi

# Initialize Kiwi
kiwi = Kiwi()

def analyze_text_complexity(text: str) -> dict:
    if not text.strip():
        return {
            "k_ar_level": 0,
            "sentence_count": 0,
            "word_count": 0,
            "avg_sentence_length": 0,
            "complex_word_ratio": 0,
            "summary": "텍스트가 입력되지 않았습니다."
        }

    # Split into sentences
    sentences = kiwi.split_into_sents(text)
    sentence_count = len(sentences)
    
    # Tokenize and analyze words
    tokens = kiwi.tokenize(text)
    
    # Filter out punctuations and whitespaces to get actual words/morphemes
    valid_pos = ['NNG', 'NNP', 'NNB', 'NR', 'NP', 'VV', 'VA', 'VX', 'VCP', 'VCN', 'MM', 'MAG', 'MAJ', 'IC']
    words = [token for token in tokens if token.tag in valid_pos]
    word_count = len(words)
    
    if sentence_count == 0 or word_count == 0:
        return {
            "k_ar_level": 0,
            "sentence_count": sentence_count,
            "word_count": word_count,
            "avg_sentence_length": 0,
            "complex_word_ratio": 0,
            "summary": "유효한 문장이나 단어가 없습니다."
        }

    # Average sentence length (in morphemes)
    avg_sentence_length = word_count / sentence_count
    
    # Define complex words simply as longer words or specific POS tags (e.g., Hanja nouns NNG with length > 2)
    # A real implementation would use a graded vocabulary list.
    complex_words = [w for w in words if len(w.form) >= 3 and w.tag in ['NNG', 'NNP', 'VV', 'VA']]
    complex_word_ratio = len(complex_words) / word_count if word_count > 0 else 0

    # K-AR Formula (Mock heuristic)
    # Average sentence length contributes to 40% of the score (normalized to 1-10 level, assume max ~ 20 words/sentence)
    # Complex word ratio contributes to 60% of the score (assume max ~ 0.3)
    
    sl_score = min(avg_sentence_length / 2.0, 10)  # max out around 20 words per sentence
    cw_score = min((complex_word_ratio / 0.3) * 10, 10)
    
    k_ar_level = round((sl_score * 0.4) + (cw_score * 0.6), 1)
    
    # Ensure it's bounded 1.0 - 12.0 (like AR level)
    k_ar_level = max(1.0, min(12.0, k_ar_level))

    return {
        "k_ar_level": k_ar_level,
        "sentence_count": sentence_count,
        "word_count": word_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "complex_word_ratio": round(complex_word_ratio, 3),
        "summary": f"이 글은 K-AR {k_ar_level} 레벨 수준입니다."
    }
