import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Lesson, Quiz, Flashcard, Progress

app = FastAPI(title="LangLearn API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "LangLearn API is running"}

# Health & schema endpoints
@app.get("/schema")
def get_schema():
    return {
        "lesson": Lesson.model_json_schema(),
        "quiz": Quiz.model_json_schema(),
        "flashcard": Flashcard.model_json_schema(),
        "progress": Progress.model_json_schema(),
    }

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Helper to convert ObjectId to str in results

def serialize(doc: Dict[str, Any]):
    if not doc:
        return doc
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    return out

# Seed some demo content if empty
@app.post("/seed")
def seed_demo():
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        # Seed lessons
        if db["lesson"].count_documents({}) == 0:
            lessons = [
                {
                    "language": "Spanish",
                    "title": "Basics: Greetings",
                    "level": "A1",
                    "content": "Hola, ¿cómo estás? Learn common greetings and introductions.",
                    "objectives": ["Greet someone", "Introduce yourself", "Say goodbye"],
                },
                {
                    "language": "French",
                    "title": "Basics: Numbers",
                    "level": "A1",
                    "content": "Un, deux, trois... Learn numbers 1-20 with pronunciation tips.",
                    "objectives": ["Count to 20", "Ask and tell age"],
                },
            ]
            for l in lessons:
                create_document("lesson", l)
        # Seed flashcards
        if db["flashcard"].count_documents({}) == 0:
            cards = [
                {"language": "Spanish", "term": "Hola", "definition": "Hello", "example": "Hola, Juan!"},
                {"language": "Spanish", "term": "Adiós", "definition": "Goodbye", "example": "Adiós, hasta mañana."},
                {"language": "French", "term": "Merci", "definition": "Thank you", "example": "Merci beaucoup!"},
            ]
            for c in cards:
                create_document("flashcard", c)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Lessons
@app.get("/lessons")
def list_lessons(language: Optional[str] = None, level: Optional[str] = None):
    q: Dict[str, Any] = {}
    if language:
        q["language"] = language
    if level:
        q["level"] = level
    items = [serialize(d) for d in get_documents("lesson", q)]
    return {"items": items}

@app.post("/lessons")
def create_lesson(payload: Lesson):
    _id = create_document("lesson", payload)
    return {"id": _id}

# Quizzes
@app.get("/quizzes")
def list_quizzes(lesson_id: Optional[str] = None):
    q: Dict[str, Any] = {}
    if lesson_id:
        q["lesson_id"] = lesson_id
    items = [serialize(d) for d in get_documents("quiz", q)]
    return {"items": items}

@app.post("/quizzes")
def create_quiz(payload: Quiz):
    _id = create_document("quiz", payload)
    return {"id": _id}

# Flashcards
@app.get("/flashcards")
def list_flashcards(language: Optional[str] = None, limit: int = 50):
    q: Dict[str, Any] = {}
    if language:
        q["language"] = language
    items = [serialize(d) for d in get_documents("flashcard", q, limit=limit)]
    return {"items": items}

@app.post("/flashcards")
def create_flashcard(payload: Flashcard):
    _id = create_document("flashcard", payload)
    return {"id": _id}

# Progress
@app.get("/progress/{user_id}")
def get_progress(user_id: str):
    items = [serialize(d) for d in get_documents("progress", {"user_id": user_id}, limit=1)]
    return items[0] if items else {"user_id": user_id, "streak_days": 0, "completed": False}

class ProgressUpdate(BaseModel):
    user_id: str
    lesson_id: Optional[str] = None
    quiz_score: Optional[float] = None
    completed: Optional[bool] = None
    streak_days: Optional[int] = None
    studied_flashcards: Optional[int] = None

@app.post("/progress")
def update_progress(payload: ProgressUpdate):
    # Upsert-like behavior: create a new progress snapshot document
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    _id = create_document("progress", data)
    return {"id": _id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
