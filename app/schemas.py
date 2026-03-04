from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- Song Schemas ---
class SongCreate(BaseModel):
    title: str
    artist: str
    genre: str
    release_year: Optional[int] = None
    album: Optional[str] = None
    popularity: Optional[int] = None
    duration_ms: Optional[int] = None
    explicit: Optional[bool] = False
    danceability: Optional[float] = None
    energy: Optional[float] = None
    valence: Optional[float] = None
    tempo: Optional[float] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    liveness: Optional[float] = None
    speechiness: Optional[float] = None


class SongResponse(SongCreate):
    id: int
    track_id: Optional[str] = None

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


# --- Recommendation Schema ---
class RecommendationResponse(BaseModel):
    id: int
    title: str
    artist: str
    genre: str
    valence: Optional[float]
    energy: Optional[float]
    tempo: Optional[float]
    danceability: Optional[float]
    popularity: Optional[int]
    mood_match: str

    class Config:
        from_attributes = True

# --- Journey Schemas ---
class JourneyRequest(BaseModel):
    description: str
    total_songs: Optional[int] = 15

class JourneyStage(BaseModel):
    stage: str
    description: str
    duration_songs: int
    audio_profile: dict
    songs: List[RecommendationResponse] = []

class JourneyResponse(BaseModel):
    journey_title: str
    description: str
    total_songs: int
    ai_reasoning: str
    stages: List[JourneyStage]