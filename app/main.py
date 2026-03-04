from fastapi import FastAPI, Depends, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app import models, schemas
from app.database import engine, get_db
from dotenv import load_dotenv
import anthropic
import os
import json

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
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
# API KEY AUTHENTICATION
# ─────────────────────────────────────────

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_SECRET_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key. Include your key in the X-API-Key header."
        )
    return api_key

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

@app.get("/analytics/top-genres", dependencies=[Depends(require_api_key)])
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


@app.get("/analytics/mood-trends", dependencies=[Depends(require_api_key)])
def mood_trends(db: Session = Depends(get_db)):
    results = (
        db.query(models.Mood.name, func.count(models.Log.id).label("count"))
        .join(models.Log, models.Log.mood_id == models.Mood.id)
        .group_by(models.Mood.name)
        .order_by(func.count(models.Log.id).desc())
        .all()
    )
    return [{"mood": r[0], "count": r[1]} for r in results]

@app.get("/analytics/top-songs", dependencies=[Depends(require_api_key)])
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

# ─────────────────────────────────────────
# NATURAL LANGUAGE SEARCH (Claude AI)
# ─────────────────────────────────────────

@app.get("/search/natural", dependencies=[Depends(require_api_key)])
async def natural_language_search(
    query: str = Query(..., description="Describe how you feel or what you want e.g. 'something chill for late night studying'"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Natural language music search powered by Claude AI.
    Describe a mood, activity, or feeling in plain English and get matching Spotify tracks.
    """

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are a music recommendation AI with deep knowledge of Spotify audio features.

A user wants music for this situation: "{query}"

Analyse this request and return ONLY a valid JSON object (no explanation, no markdown) with Spotify audio feature thresholds to filter songs. Use these fields:
- valence_min / valence_max (0.0-1.0): musical positivity
- energy_min / energy_max (0.0-1.0): intensity and activity  
- tempo_min / tempo_max (BPM, typically 60-200)
- danceability_min / danceability_max (0.0-1.0)
- acousticness_min / acousticness_max (0.0-1.0)
- reasoning: one sentence explaining your choices

Only include fields that are relevant. For example a sad song needs valence_max but not valence_min.

Example output:
{{"valence_max": 0.4, "energy_max": 0.5, "reasoning": "Sad songs have low positivity and low intensity"}}

Now analyse: "{query}"
"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()

        # Robustly extract JSON
        if "```" in raw:
            raw = raw.replace("```json", "").replace("```", "").strip()

        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise HTTPException(status_code=500, detail=f"No JSON found in response: {raw[:200]}")
        raw = raw[start:end]

        journey_plan = json.loads(raw)

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"JSON parse failed: {str(e)} | Raw: {raw[:200]}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {str(e)}"
        )

    # Build database query from Claude's profile
    song_query = db.query(models.Song).filter(models.Song.valence != None)

    if "valence_min" in profile:
        song_query = song_query.filter(models.Song.valence >= profile["valence_min"])
    if "valence_max" in profile:
        song_query = song_query.filter(models.Song.valence <= profile["valence_max"])
    if "energy_min" in profile:
        song_query = song_query.filter(models.Song.energy >= profile["energy_min"])
    if "energy_max" in profile:
        song_query = song_query.filter(models.Song.energy <= profile["energy_max"])
    if "tempo_min" in profile:
        song_query = song_query.filter(models.Song.tempo >= profile["tempo_min"])
    if "tempo_max" in profile:
        song_query = song_query.filter(models.Song.tempo <= profile["tempo_max"])
    if "danceability_min" in profile:
        song_query = song_query.filter(models.Song.danceability >= profile["danceability_min"])
    if "danceability_max" in profile:
        song_query = song_query.filter(models.Song.danceability <= profile["danceability_max"])
    if "acousticness_min" in profile:
        song_query = song_query.filter(models.Song.acousticness >= profile["acousticness_min"])
    if "acousticness_max" in profile:
        song_query = song_query.filter(models.Song.acousticness <= profile["acousticness_max"])

    results = song_query.order_by(
        models.Song.popularity.desc()
    ).limit(limit).all()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No songs matched your description. Try a different query."
        )

    return {
        "query": query,
        "ai_reasoning": reasoning,
        "audio_profile": profile,
        "results": [
            {
                "id": s.id,
                "title": s.title,
                "artist": s.artist,
                "genre": s.genre,
                "popularity": s.popularity,
                "valence": s.valence,
                "energy": s.energy,
                "tempo": round(s.tempo, 1) if s.tempo else None,
                "danceability": s.danceability,
                "acousticness": s.acousticness,
            }
            for s in results
        ]
    }

# ─────────────────────────────────────────
# MOOD JOURNEY — AI PLAYLIST ARCHITECT
# ─────────────────────────────────────────

@app.post("/journey", dependencies=[Depends(require_api_key)])
async def create_mood_journey(
    request: schemas.JourneyRequest,
    db: Session = Depends(get_db)
):
    """
    AI-powered mood journey playlist generator.
    Describe an experience or activity and Claude will architect
    a multi-stage playlist that evolves with your emotional arc.
    """

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are an expert music curator and psychologist who understands emotional arcs in human experiences.

A user wants a playlist for this experience: "{request.description}"
Total songs requested: {request.total_songs}

Analyse the emotional arc of this experience and break it into 2-4 meaningful stages.
For each stage, define Spotify audio feature thresholds that match that emotional moment.

Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{{
  "journey_title": "Short evocative title for this journey",
  "ai_reasoning": "One sentence explaining the emotional arc you identified",
  "stages": [
    {{
      "stage": "Stage name",
      "description": "What this stage feels like emotionally",
      "duration_songs": <number of songs, must sum to {request.total_songs}>,
      "audio_profile": {{
        "valence_min": <optional, 0.0-1.0>,
        "valence_max": <optional, 0.0-1.0>,
        "energy_min": <optional, 0.0-1.0>,
        "energy_max": <optional, 0.0-1.0>,
        "tempo_min": <optional, 60-200>,
        "tempo_max": <optional, 60-200>,
        "danceability_min": <optional, 0.0-1.0>,
        "danceability_max": <optional, 0.0-1.0>,
        "acousticness_min": <optional, 0.0-1.0>,
        "acousticness_max": <optional, 0.0-1.0>
      }}
    }}
  ]
}}

Only include audio feature fields that are genuinely relevant to each stage.
Make sure duration_songs values sum exactly to {request.total_songs}.
Now analyse: "{request.description}"
"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()

        # Robustly strip markdown code fences
        if "```" in raw:
            # Extract content between first ``` and last ```
            raw = raw.replace("```json", "").replace("```", "").strip()

        # Find the first { and last } to extract pure JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise json.JSONDecodeError("No JSON found", raw, 0)
        raw = raw[start:end]

        journey_plan = json.loads(raw)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned unexpected format. Please try rephrasing your description."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI service error: {str(e)}"
        )

    # Build playlist for each stage
    stages_with_songs = []
    total_found = 0

    for stage in journey_plan.get("stages", []):
        profile = stage.get("audio_profile", {})
        n_songs = stage.get("duration_songs", 3)

        song_query = db.query(models.Song).filter(models.Song.valence != None)

        if "valence_min" in profile:
            song_query = song_query.filter(models.Song.valence >= profile["valence_min"])
        if "valence_max" in profile:
            song_query = song_query.filter(models.Song.valence <= profile["valence_max"])
        if "energy_min" in profile:
            song_query = song_query.filter(models.Song.energy >= profile["energy_min"])
        if "energy_max" in profile:
            song_query = song_query.filter(models.Song.energy <= profile["energy_max"])
        if "tempo_min" in profile:
            song_query = song_query.filter(models.Song.tempo >= profile["tempo_min"])
        if "tempo_max" in profile:
            song_query = song_query.filter(models.Song.tempo <= profile["tempo_max"])
        if "danceability_min" in profile:
            song_query = song_query.filter(models.Song.danceability >= profile["danceability_min"])
        if "danceability_max" in profile:
            song_query = song_query.filter(models.Song.danceability <= profile["danceability_max"])
        if "acousticness_min" in profile:
            song_query = song_query.filter(models.Song.acousticness >= profile["acousticness_min"])
        if "acousticness_max" in profile:
            song_query = song_query.filter(models.Song.acousticness <= profile["acousticness_max"])

        songs = song_query.order_by(
            models.Song.popularity.desc()
        ).limit(n_songs).all()

        total_found += len(songs)

        stages_with_songs.append({
            "stage": stage.get("stage", "Stage"),
            "description": stage.get("description", ""),
            "duration_songs": n_songs,
            "audio_profile": profile,
            "songs": [
                {
                    "id": s.id,
                    "title": s.title,
                    "artist": s.artist,
                    "genre": s.genre,
                    "popularity": s.popularity,
                    "valence": s.valence,
                    "energy": s.energy,
                    "tempo": round(s.tempo, 1) if s.tempo else None,
                    "danceability": s.danceability,
                    "mood_match": stage.get("stage", "")
                }
                for s in songs
            ]
        })

    return {
        "journey_title": journey_plan.get("journey_title", "Your Journey"),
        "description": request.description,
        "total_songs": total_found,
        "ai_reasoning": journey_plan.get("ai_reasoning", ""),
        "stages": stages_with_songs
    }