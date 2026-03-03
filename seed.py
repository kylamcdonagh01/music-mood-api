from app.database import SessionLocal
from app import models, database

# Create all tables if they don't exist
database.engine.connect()
models.Base.metadata.create_all(bind=database.engine)

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
    exists = db.query(models.Mood).filter(models.Mood.name == m["name"]).first()
    if not exists:
        db.add(models.Mood(**m))

db.commit()

# ── Songs ──────────────────────────────────────────
songs = [
    {"title": "Blinding Lights",        "artist": "The Weeknd",         "genre": "Pop",       "release_year": 2019},
    {"title": "HUMBLE.",                "artist": "Kendrick Lamar",      "genre": "Hip-Hop",   "release_year": 2017},
    {"title": "Lose Yourself",          "artist": "Eminem",              "genre": "Hip-Hop",   "release_year": 2002},
    {"title": "Levitating",             "artist": "Dua Lipa",            "genre": "Pop",       "release_year": 2020},
    {"title": "Bohemian Rhapsody",      "artist": "Queen",               "genre": "Rock",      "release_year": 1975},
    {"title": "Shape of You",           "artist": "Ed Sheeran",          "genre": "Pop",       "release_year": 2017},
    {"title": "God's Plan",             "artist": "Drake",               "genre": "Hip-Hop",   "release_year": 2018},
    {"title": "Someone Like You",       "artist": "Adele",               "genre": "Soul",      "release_year": 2011},
    {"title": "Smells Like Teen Spirit","artist": "Nirvana",             "genre": "Rock",      "release_year": 1991},
    {"title": "Watermelon Sugar",       "artist": "Harry Styles",        "genre": "Pop",       "release_year": 2019},
    {"title": "Bad Guy",                "artist": "Billie Eilish",       "genre": "Pop",       "release_year": 2019},
    {"title": "Hotline Bling",          "artist": "Drake",               "genre": "Hip-Hop",   "release_year": 2015},
    {"title": "Clocks",                 "artist": "Coldplay",            "genre": "Rock",      "release_year": 2002},
    {"title": "Rolling in the Deep",    "artist": "Adele",               "genre": "Soul",      "release_year": 2010},
    {"title": "Sicko Mode",             "artist": "Travis Scott",        "genre": "Hip-Hop",   "release_year": 2018},
    {"title": "Titanium",               "artist": "David Guetta",        "genre": "Electronic","release_year": 2011},
    {"title": "Lean On",                "artist": "Major Lazer",         "genre": "Electronic","release_year": 2015},
    {"title": "Mr. Brightside",         "artist": "The Killers",         "genre": "Rock",      "release_year": 2003},
    {"title": "Stay With Me",           "artist": "Sam Smith",           "genre": "Soul",      "release_year": 2014},
    {"title": "Uptown Funk",            "artist": "Bruno Mars",          "genre": "Funk",      "release_year": 2014},
]

for s in songs:
    exists = db.query(models.Song).filter(
        models.Song.title == s["title"],
        models.Song.artist == s["artist"]
    ).first()
    if not exists:
        db.add(models.Song(**s))

db.commit()

# ── Logs ──────────────────────────────────────────
logs = [
    {"song_id": 1,  "mood_id": 1, "user_label": "Morning run"},
    {"song_id": 2,  "mood_id": 3, "user_label": "Gym session"},
    {"song_id": 3,  "mood_id": 3, "user_label": "Workout motivation"},
    {"song_id": 4,  "mood_id": 1, "user_label": "Weekend vibes"},
    {"song_id": 5,  "mood_id": 4, "user_label": "Sunday evening"},
    {"song_id": 6,  "mood_id": 1, "user_label": "Party playlist"},
    {"song_id": 7,  "mood_id": 4, "user_label": "Late night drive"},
    {"song_id": 8,  "mood_id": 2, "user_label": "Rainy day"},
    {"song_id": 9,  "mood_id": 5, "user_label": "Frustrating day"},
    {"song_id": 10, "mood_id": 1, "user_label": "Summer playlist"},
    {"song_id": 11, "mood_id": 4, "user_label": "Chill studying"},
    {"song_id": 12, "mood_id": 1, "user_label": "Friday night"},
    {"song_id": 13, "mood_id": 4, "user_label": "Focus time"},
    {"song_id": 14, "mood_id": 2, "user_label": "Heartbreak playlist"},
    {"song_id": 15, "mood_id": 3, "user_label": "Pre-match hype"},
    {"song_id": 16, "mood_id": 3, "user_label": "Dance floor"},
    {"song_id": 17, "mood_id": 1, "user_label": "Festival vibes"},
    {"song_id": 18, "mood_id": 5, "user_label": "Intense mood"},
    {"song_id": 19, "mood_id": 2, "user_label": "Missing someone"},
    {"song_id": 20, "mood_id": 1, "user_label": "Good times"},
]

for l in logs:
    db.add(models.Log(**l))

db.commit()
db.close()

print("✅ Database seeded successfully with 5 moods, 20 songs, and 20 logs.")
