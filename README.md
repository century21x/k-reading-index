# K-Reading Index

![CI](https://github.com/century21x/k-reading-index/actions/workflows/ci.yml/badge.svg)

한국어 학습자(KSL)를 위한 **읽기 실력 진단** 및 **텍스트 난이도 분석** 웹 앱입니다.

- **K-Reading Test** — 적응형 독해 시험 → TOPIK 읽기 수준 추정 (1.0 ~ 6.0)
- **Text Analyzer** — 한국어 지문의 K-AR 난이도 분석 (형태소 기반)

**Live demo:** Render 등에 배포 후 URL을 이곳에 추가하세요.

Repository: [github.com/century21x/k-reading-index](https://github.com/century21x/k-reading-index)

---

## Features

| Mode | Description |
|------|-------------|
| K-Reading Test | Read passages, answer MCQs, adaptive TOPIK level estimate |
| Text Analyzer | Paste Korean text → sentence stats + K-AR level |

---

## Quick Start

### Requirements

- Python 3.10+
- pip

### Install & Run

```bash
git clone https://github.com/century21x/k-reading-index.git
cd k-reading-index
pip install -r requirements.txt

cd backend
python scripts/import_passages.py
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open in browser:

| Page | URL |
|------|-----|
| Home | http://localhost:8000/ |
| Reading Test | http://localhost:8000/test.html |
| Text Analyzer | http://localhost:8000/analyze.html |
| API docs | http://localhost:8000/docs |

---

## API Overview

### Text analysis

```http
POST /api/analyze
Content-Type: application/json

{ "text": "분석할 한국어 텍스트" }
```

### Adaptive reading test

```http
POST /api/test/sessions
{ "native_language": "en", "korean_study_months": 6 }

POST /api/test/sessions/{session_id}/answers
{ "question_id": 1, "choice_id": 4 }

GET /api/test/sessions/{session_id}/result
```

---

## Project Structure

```
k-reading-index/
├── README.md
├── requirements.txt
├── render.yaml          # Render.com deploy
├── Dockerfile
└── backend/
    ├── main.py
    ├── analyzer.py
    ├── database/        # SQLite schema & seeds
    ├── models/
    ├── routers/
    ├── services/        # TOPIK adaptive engine
    ├── scripts/         # import_passages.py
    ├── seeds/           # sample passages (6)
    └── static/          # Web UI
```

---

## Seed Data

Import sample passages (6 texts × 5 questions):

```bash
cd backend
python scripts/import_passages.py
python scripts/import_passages.py --file seeds/eps_template.json --dry-run
```

To add your own content, follow the JSON format in `backend/seeds/sample_passages.json`.

---

## Deployment

### Render (recommended)

1. Fork or use this repo on GitHub.
2. [Render Dashboard](https://dashboard.render.com/) → **New → Blueprint**
3. Connect `century21x/k-reading-index` — `render.yaml` is applied automatically.
4. After deploy, open the generated URL.

Or manually: **New Web Service** → Build: `pip install -r requirements.txt && cd backend && python scripts/import_passages.py` → Start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

### Docker

```bash
docker build -t k-reading-index .
docker run -p 8000:8000 k-reading-index
```

### GitHub Pages

This project is a **full-stack FastAPI app** (API + SQLite). GitHub Pages hosts static files only and cannot run the Python backend. Use Render, Railway, Fly.io, or Docker instead.

---

## CI

GitHub Actions runs on every push/PR to `master`:

- Install dependencies
- Import seed passages
- Smoke-test `/api/analyze` and `/api/test/sessions`

---

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **NLP:** KiwiPiePy (Korean morphological analysis)
- **Frontend:** Vanilla HTML / CSS / JavaScript

---

## License

No license file yet. Contact the repository owner before commercial use.
