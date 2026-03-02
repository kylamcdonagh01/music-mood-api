from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- Song Schemas ---
class SongCreate(BaseModel):
    title: str
    artist: str
    genre: str
    release_year: int

class SongResponse(SongCreate):
    id: int

    class Config:
        from_attributes = True


# --- Mood Schemas ---
class MoodCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MoodResponse(MoodCreate):
    id: int

    class Config:
        from_attributes = True


# --- Log Schemas ---
class LogCreate(BaseModel):
    song_id: int
    mood_id: int
    user_label: Optional[str] = None

class LogUpdate(BaseModel):
    mood_id: int
    user_label: Optional[str] = None

class LogResponse(BaseModel):
    id: int
    song_id: int
    mood_id: int
    user_label: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True