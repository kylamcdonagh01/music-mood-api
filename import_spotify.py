import csv
import sys
from app.database import SessionLocal
from app import models, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

db = SessionLocal()

print("🎵 Starting Spotify dataset import...")
print("This may take a minute — importing up to 50,000 tracks...")

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

def safe_bool(val):
    return str(val).strip().lower() == "true"

imported = 0
skipped = 0
seen_track_ids = set()
LIMIT = 50000  # import 50k songs — plenty for a great demo

with open("dataset.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if imported >= LIMIT:
            break

        track_id = row.get("track_id", "").strip()
        title = row.get("track_name", "").strip()
        artist = row.get("artists", "").strip()
        genre = row.get("track_genre", "").strip()

        # Skip rows with missing essential data
        if not track_id or not title or not artist or not genre:
            skipped += 1
            continue

        # Skip duplicate track_ids
        if track_id in seen_track_ids:
            skipped += 1
            continue
        seen_track_ids.add(track_id)

        song = models.Song(
            track_id=track_id,
            title=title,
            artist=artist,
            album=row.get("album_name", "").strip(),
            genre=genre,
            popularity=safe_int(row.get("popularity")),
            duration_ms=safe_int(row.get("duration_ms")),
            explicit=safe_bool(row.get("explicit")),
            danceability=safe_float(row.get("danceability")),
            energy=safe_float(row.get("energy")),
            valence=safe_float(row.get("valence")),
            tempo=safe_float(row.get("tempo")),
            acousticness=safe_float(row.get("acousticness")),
            instrumentalness=safe_float(row.get("instrumentalness")),
            liveness=safe_float(row.get("liveness")),
            speechiness=safe_float(row.get("speechiness")),
        )
        db.add(song)
        imported += 1

        # Commit in batches of 1000 for speed
        if imported % 1000 == 0:
            db.commit()
            print(f"  ✅ {imported} songs imported...")

db.commit()
db.close()
print(f"\n🎉 Done! Imported {imported} songs, skipped {skipped} duplicates/invalid rows.")
