INSERT OR REPLACE INTO question_types (code, label_ko, label_en, topik_section, difficulty_weight, sort_order) VALUES
('topic_identification', '주제·장소 파악', 'Topic / setting', 'reading', 1.0, 1),
('content_match', '내용 일치', 'Content match', 'reading', 1.0, 2),
('content_mismatch', '내용 불일치', 'Content mismatch', 'reading', 1.1, 3),
('sequencing', '순서 배열', 'Sequencing', 'reading', 1.2, 4),
('fill_blank', '빈칸 추론', 'Fill in the blank', 'reading', 1.2, 5),
('main_idea', '중심 내용', 'Main idea', 'reading', 1.1, 6),
('detail', '세부 정보', 'Detail', 'reading', 1.0, 7),
('inference', '추론', 'Inference', 'reading', 1.3, 8),
('vocabulary_context', '어휘 문맥', 'Vocabulary in context', 'reading', 1.0, 9),
('practical_info', '실용 정보', 'Practical info', 'reading', 0.9, 10);
