from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from analyzer import analyze_text_complexity
import os

app = FastAPI(title="K-Reading Index API", description="한국어 텍스트 난이도 측정 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

@app.post("/api/analyze")
def analyze(request: TextRequest):
    result = analyze_text_complexity(request.text)
    return result

# Create static dir if not exists
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
