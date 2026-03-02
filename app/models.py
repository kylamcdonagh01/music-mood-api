from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    release_year = Column(Integer, nullable=False)

    logs = relationship("Log", back_populates="song")


class Mood(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

    logs = relationship("Log", back_populates="mood")


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    mood_id = Column(Integer, ForeignKey("moods.id"), nullable=False)
    user_label = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    song = relationship("Song", back_populates="logs")
    mood = relationship("Mood", back_populates="logs")