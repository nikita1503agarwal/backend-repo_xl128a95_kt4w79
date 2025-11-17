"""
Database Schemas for the Language E‑Learning app

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercase of the model class name (e.g., Lesson -> "lesson").
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Core domain models
class Lesson(BaseModel):
    language: str = Field(..., description="Language code or name (e.g., 'Spanish')")
    title: str = Field(..., description="Lesson title")
    level: str = Field(..., description="Difficulty level: A1, A2, B1, B2, C1, C2")
    content: str = Field(..., description="Rich text/markdown lesson content")
    objectives: List[str] = Field(default_factory=list, description="What you will learn")

class Quiz(BaseModel):
    lesson_id: str = Field(..., description="Related lesson id as string")
    questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of questions: {id, prompt, options, answer, type}"
    )

class Flashcard(BaseModel):
    language: str = Field(..., description="Language code or name")
    term: str = Field(..., description="Front of the card")
    definition: str = Field(..., description="Back of the card")
    example: Optional[str] = Field(None, description="Usage example")

class Progress(BaseModel):
    user_id: str = Field(..., description="Client-generated anonymous user id")
    lesson_id: Optional[str] = Field(None, description="Related lesson id")
    quiz_score: Optional[float] = Field(None, description="Score percentage 0-100")
    completed: bool = Field(False, description="Lesson completed")
    streak_days: int = Field(0, description="Learning streak days")
    studied_flashcards: int = Field(0, description="Count of studied cards today")
