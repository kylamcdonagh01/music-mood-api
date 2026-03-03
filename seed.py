from app.database import SessionLocal, engine
from app.database import Base
from app.models import Song, Mood, Log

# Create all tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ── Moods ──────────────────────────────────────────
moods = [
    {"name": "happy",     "description": "Feeling joyful and upbeat"},
    {"name": "sad",       "description": "Feeling low or emotional"},
    {"name": "energetic", "description": "Feeling pumped and motivated"},
    {"name": "calm",      "description": "Feeling relaxed and peaceful"},
    {"name": "angry",     "description": "Feeling frustrated or intense"},
]

for m in moods:
    exists = db.query(Mood).filter(Mood.name == m["name"]).first()
    if not exists:
        db.add(Mood(**m))

db.commit()
db.close()

print("✅ Moods seeded successfully.")
