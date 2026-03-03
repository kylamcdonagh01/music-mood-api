from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app import models, schemas
from app.database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Music Mood API",
    description="A data-driven API for discovering music by mood, powered by 50,000 real Spotify tracks.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# SONGS
# ─────────────────────────────────────────

@app.post("/songs", response_model=schemas.SongResponse, status_code=201)
def create_song(song: schemas.SongCreate, db: Session = Depends(get_db)):
    db_song = models.Song(**song.model_dump())
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song


@app.get("/songs", response_model=List[schemas.SongResponse])
def get_songs(
    genre: str = None,
    artist: str = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Song)
    if genre:
        query = query.filter(models.Song.genre.ilike(f"%{genre}%"))
    if artist:
        query = query.filter(models.Song.artist.ilike(f"%{artist}%"))
    if search:
        query = query.filter(models.Song.title.ilike(f"%{search}%"))
    return query.all()

@app.get("/songs/{song_id}", response_model=schemas.SongResponse)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


# ─────────────────────────────────────────
# MOODS
# ─────────────────────────────────────────

@app.post("/moods", response_model=schemas.MoodResponse, status_code=201)
def create_mood(mood: schemas.MoodCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Mood).filter(models.Mood.name == mood.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mood already exists")
    db_mood = models.Mood(**mood.model_dump())
    db.add(db_mood)
    db.commit()
    db.refresh(db_mood)
    return db_mood


@app.get("/moods", response_model=List[schemas.MoodResponse])
def get_moods(db: Session = Depends(get_db)):
    return db.query(models.Mood).all()


# ─────────────────────────────────────────
# LOGS (full CRUD)
# ─────────────────────────────────────────

@app.post("/logs", response_model=schemas.LogResponse, status_code=201)
def create_log(log: schemas.LogCreate, db: Session = Depends(get_db)):
    song = db.query(models.Song).filter(models.Song.id == log.song_id).first()
    mood = db.query(models.Mood).filter(models.Mood.id == log.mood_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    if not mood:
        raise HTTPException(status_code=404, detail="Mood not found")
    db_log = models.Log(**log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@app.get("/logs", response_model=List[schemas.LogResponse])
def get_logs(db: Session = Depends(get_db)):
    return db.query(models.Log).all()


@app.put("/logs/{log_id}", response_model=schemas.LogResponse)
def update_log(log_id: int, log_update: schemas.LogUpdate, db: Session = Depends(get_db)):
    log = db.query(models.Log).filter(models.Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    mood = db.query(models.Mood).filter(models.Mood.id == log_update.mood_id).first()
    if not mood:
        raise HTTPException(status_code=404, detail="Mood not found")
    log.mood_id = log_update.mood_id
    log.user_label = log_update.user_label
    db.commit()
    db.refresh(log)
    return log


@app.delete("/logs/{log_id}", status_code=204)
def delete_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(models.Log).filter(models.Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    db.delete(log)
    db.commit()


# ─────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────

@app.get("/analytics/top-genres")
def top_genres_by_mood(db: Session = Depends(get_db)):
    results = (
        db.query(models.Song.genre, models.Mood.name, func.count(models.Log.id).label("count"))
        .join(models.Log, models.Log.song_id == models.Song.id)
        .join(models.Mood, models.Log.mood_id == models.Mood.id)
        .group_by(models.Song.genre, models.Mood.name)
        .order_by(func.count(models.Log.id).desc())
        .all()
    )
    return [{"genre": r[0], "mood": r[1], "count": r[2]} for r in results]


@app.get("/analytics/mood-trends")
def mood_trends(db: Session = Depends(get_db)):
    results = (
        db.query(models.Mood.name, func.count(models.Log.id).label("count"))
        .join(models.Log, models.Log.mood_id == models.Mood.id)
        .group_by(models.Mood.name)
        .order_by(func.count(models.Log.id).desc())
        .all()
    )
    return [{"mood": r[0], "count": r[1]} for r in results]

@app.get("/analytics/top-songs")
def top_songs(limit: int = 10, db: Session = Depends(get_db)):
    results = (
        db.query(models.Song.title, models.Song.artist, func.count(models.Log.id).label("log_count"))
        .join(models.Log, models.Log.song_id == models.Song.id)
        .group_by(models.Song.id)
        .order_by(func.count(models.Log.id).desc())
        .limit(limit)
        .all()
    )
    return [{"title": r[0], "artist": r[1], "log_count": r[2]} for r in results]

# ─────────────────────────────────────────
# MOOD-BASED RECOMMENDATIONS
# ─────────────────────────────────────────

# Mood profiles — maps mood names to Spotify audio feature thresholds
MOOD_PROFILES = {
    "happy": {
        "valence_min": 0.6,
        "energy_min": 0.5,
        "description": "High valence and energy — joyful, upbeat tracks"
    },
    "sad": {
        "valence_max": 0.4,
        "energy_max": 0.5,
        "description": "Low valence and energy — emotional, melancholic tracks"
    },
    "energetic": {
        "energy_min": 0.8,
        "tempo_min": 120.0,
        "description": "Very high energy and fast tempo — workout and hype tracks"
    },
    "calm": {
        "energy_max": 0.4,
        "tempo_max": 100.0,
        "description": "Low energy and slow tempo — relaxing, peaceful tracks"
    },
    "angry": {
        "valence_max": 0.4,
        "energy_min": 0.8,
        "description": "Low valence, very high energy — intense, aggressive tracks"
    },
}


@app.get("/recommendations", response_model=List[schemas.RecommendationResponse])
def get_recommendations(
    mood: str = Query(..., description="Mood name: happy, sad, energetic, calm, or angry"),
    genre: Optional[str] = Query(None, description="Optional genre filter e.g. pop, rock, hip-hop"),
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations (1-50)"),
    db: Session = Depends(get_db)
):
    mood_lower = mood.lower()
    if mood_lower not in MOOD_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown mood '{mood}'. Choose from: {', '.join(MOOD_PROFILES.keys())}"
        )

    profile = MOOD_PROFILES[mood_lower]
    query = db.query(models.Song).filter(models.Song.valence != None)

    # Apply mood filters based on profile
    if "valence_min" in profile:
        query = query.filter(models.Song.valence >= profile["valence_min"])
    if "valence_max" in profile:
        query = query.filter(models.Song.valence <= profile["valence_max"])
    if "energy_min" in profile:
        query = query.filter(models.Song.energy >= profile["energy_min"])
    if "energy_max" in profile:
        query = query.filter(models.Song.energy <= profile["energy_max"])
    if "tempo_min" in profile:
        query = query.filter(models.Song.tempo >= profile["tempo_min"])
    if "tempo_max" in profile:
        query = query.filter(models.Song.tempo <= profile["tempo_max"])

    # Optional genre filter
    if genre:
        query = query.filter(models.Song.genre.ilike(f"%{genre}%"))

    # Order by popularity so we get well-known tracks first
    results = query.order_by(models.Song.popularity.desc()).limit(limit).all()

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No songs found for mood '{mood}' with the given filters."
        )

    return [
        schemas.RecommendationResponse(
            id=song.id,
            title=song.title,
            artist=song.artist,
            genre=song.genre,
            valence=song.valence,
            energy=song.energy,
            tempo=song.tempo,
            danceability=song.danceability,
            popularity=song.popularity,
            mood_match=mood_lower
        )
        for song in results
    ]


@app.get("/recommendations/explain/{mood}")
def explain_mood(mood: str):
    mood_lower = mood.lower()
    if mood_lower not in MOOD_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown mood. Choose from: {', '.join(MOOD_PROFILES.keys())}"
        )
    profile = MOOD_PROFILES[mood_lower]
    return {
        "mood": mood_lower,
        "description": profile["description"],
        "filters_applied": {k: v for k, v in profile.items() if k != "description"},
        "audio_features_explained": {
            "valence": "Musical positivity (0.0 = sad/dark, 1.0 = happy/bright)",
            "energy": "Intensity and activity level (0.0 = calm, 1.0 = intense)",
            "tempo": "Beats per minute — speed of the track"
        }
    }
