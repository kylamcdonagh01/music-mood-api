from app.database import SessionLocal, engine
from app.database import Base
from app.models import Song, Mood, Log

# Create all tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ── Moods ──────────────────────────────────────────
moods_data = [
    {"name": "happy",     "description": "Feeling joyful and upbeat"},
    {"name": "sad",       "description": "Feeling low or emotional"},
    {"name": "energetic", "description": "Feeling pumped and motivated"},
    {"name": "calm",      "description": "Feeling relaxed and peaceful"},
    {"name": "angry",     "description": "Feeling frustrated or intense"},
]

for m in moods_data:
    exists = db.query(Mood).filter(Mood.name == m["name"]).first()
    if not exists:
        db.add(Mood(**m))

db.commit()
print("✅ Moods seeded.")

# ── Sample Logs ─────────────────────────────────────
# Only add logs if none exist yet
existing_logs = db.query(Log).count()
if existing_logs == 0:
    # Get mood IDs
    mood_map = {m.name: m.id for m in db.query(Mood).all()}

    # Get some real songs from the database to log against
    songs = db.query(Song).order_by(Song.popularity.desc()).limit(50).all()

    if songs:
        import random
        random.seed(42)

        # Create 40 realistic logs spread across moods
        mood_song_pairs = [
            ("happy", 0), ("happy", 1), ("happy", 2), ("happy", 5),
            ("happy", 8), ("happy", 12), ("happy", 15), ("happy", 20),
            ("energetic", 3), ("energetic", 4), ("energetic", 6),
            ("energetic", 9), ("energetic", 13), ("energetic", 17),
            ("energetic", 22), ("energetic", 25),
            ("sad", 7), ("sad", 10), ("sad", 14), ("sad", 18),
            ("sad", 23), ("sad", 28),
            ("calm", 11), ("calm", 16), ("calm", 19), ("calm", 24),
            ("calm", 29), ("calm", 33),
            ("angry", 21), ("angry", 26), ("angry", 30), ("angry", 35),
            # Some songs logged multiple times to show trends
            ("happy", 0), ("happy", 1), ("energetic", 3),
            ("energetic", 4), ("happy", 2), ("sad", 7), ("calm", 11),
        ]

        for mood_name, song_idx in mood_song_pairs:
            if song_idx < len(songs):
                db.add(Log(
                    song_id=songs[song_idx].id,
                    mood_id=mood_map[mood_name],
                    user_label=f"Seeded log"
                ))

        db.commit()
        print(f"✅ {len(mood_song_pairs)} sample logs seeded.")
    else:
        print("⚠️ No songs found — run import_spotify.py first.")
else:
    print(f"ℹ️ Skipped logs — {existing_logs} already exist.")

db.close()
print("✅ Seed complete.")
