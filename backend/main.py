from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .ai import (
    OllamaError,
    evaluate_answer,
    generate_final_summary,
    generate_questions,
    health_check,
)
from .database import (
    create_session,
    get_session,
    get_sessions,
    init_db,
    save_evaluation,
    save_final,
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="InterviewBuddy AI",
    description="Local open-source AI mock interview partner",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class StartInterviewRequest(BaseModel):
    role: str = Field(min_length=2, max_length=100)
    difficulty: str = Field(default="Intermediate", max_length=30)
    question_count: int = Field(default=5, ge=3, le=10)
    resume_text: str = Field(default="", max_length=20000)
    resume_name: str = Field(default="Pasted resume", max_length=255)


class EvaluateRequest(BaseModel):
    session_id: int
    role: str
    question: str
    answer: str = Field(min_length=2, max_length=8000)
    resume_text: str = Field(default="", max_length=12000)


class FinalRequest(BaseModel):
    session_id: int
    role: str
    evaluations: list[dict]


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def api_health():
    return health_check()


@app.post("/api/resume/extract")
async def extract_resume(
    file: Annotated[UploadFile, File()],
):
    filename = file.filename or "resume"
    suffix = Path(filename).suffix.lower()
    content = await file.read()

    try:
        if suffix == ".txt":
            text = content.decode("utf-8", errors="ignore")

        elif suffix == ".pdf":
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(content))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)

        elif suffix == ".docx":
            from docx import Document
            import io

            doc = Document(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file. Use PDF, DOCX, or TXT.",
            )

        text = text.strip()

        if not text:
            raise HTTPException(
                status_code=400,
                detail="No readable text was found in the uploaded resume.",
            )

        return {
            "filename": filename,
            "text": text[:20000],
            "characters": len(text),
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read the resume: {exc}",
        ) from exc


@app.post("/api/interview/start")
def start_interview(payload: StartInterviewRequest):
    resume = payload.resume_text.strip()

    if len(resume) < 30:
        raise HTTPException(
            status_code=400,
            detail="Please upload a resume or paste at least a short resume/profile.",
        )

    try:
        result = generate_questions(
            resume=resume,
            role=payload.role,
            difficulty=payload.difficulty,
            count=payload.question_count,
        )

        session_id = create_session(
            role=payload.role,
            difficulty=payload.difficulty,
            resume_name=payload.resume_name,
            questions=result["questions"],
        )

        return {
            "session_id": session_id,
            "role": payload.role,
            "difficulty": payload.difficulty,
            "questions": result["questions"],
        }

    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/interview/evaluate")
def evaluate(payload: EvaluateRequest):
    try:
        result = evaluate_answer(
            role=payload.role,
            question=payload.question,
            answer=payload.answer,
            resume=payload.resume_text,
        )

        result["question"] = payload.question
        result["answer"] = payload.answer

        save_evaluation(payload.session_id, result)
        return result

    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/final")
def final_summary(payload: FinalRequest):
    try:
        result = generate_final_summary(
            role=payload.role,
            evaluations=payload.evaluations,
        )
        save_final(payload.session_id, result)
        return result

    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/sessions")
def sessions():
    return {"sessions": get_sessions()}


@app.get("/api/sessions/{session_id}")
def session(session_id: int):
    result = get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found.")
    return result
