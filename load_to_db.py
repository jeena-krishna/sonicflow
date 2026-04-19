import pandas as pd
import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="127.0.0.1",
    port="5433",
    database="sonicflow",
    user="jeena",
    password="sonicflow123"
)
cur = conn.cursor()
print("Connected to PostgreSQL")

# Step 1: Create tables
cur.execute("""
DROP TABLE IF EXISTS fact_streams CASCADE;
DROP TABLE IF EXISTS dim_tracks CASCADE;
DROP TABLE IF EXISTS dim_artists CASCADE;
DROP TABLE IF EXISTS dim_users CASCADE;
DROP TABLE IF EXISTS dim_dates CASCADE;
DROP TABLE IF EXISTS track_genres CASCADE;
""")

cur.execute("""
CREATE TABLE dim_artists (
    artist_id INTEGER PRIMARY KEY,
    artist_name TEXT NOT NULL
);
""")

cur.execute("""
CREATE TABLE dim_tracks (
    track_id TEXT PRIMARY KEY,
    track_name TEXT,
    album_name TEXT,
    artists TEXT,
    popularity INTEGER,
    duration_ms INTEGER,
    explicit BOOLEAN,
    danceability FLOAT,
    energy FLOAT,
    key INTEGER,
    loudness FLOAT,
    mode INTEGER,
    speechiness FLOAT,
    acousticness FLOAT,
    instrumentalness FLOAT,
    liveness FLOAT,
    valence FLOAT,
    tempo FLOAT,
    time_signature INTEGER
);
""")

cur.execute("""
CREATE TABLE dim_users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    country TEXT,
    plan TEXT,
    age_group TEXT,
    signup_date DATE
);
""")

cur.execute("""
CREATE TABLE dim_dates (
    date_id INTEGER PRIMARY KEY,
    full_date DATE,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    weekday TEXT,
    is_weekend BOOLEAN
);
""")

cur.execute("""
CREATE TABLE track_genres (
    track_id TEXT,
    genre TEXT
);
""")

cur.execute("""
CREATE TABLE fact_streams (
    stream_id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES dim_users(user_id),
    track_id TEXT REFERENCES dim_tracks(track_id),
    date_id INTEGER REFERENCES dim_dates(date_id),
    timestamp TIMESTAMP,
    listen_duration_ms INTEGER,
    skipped BOOLEAN,
    shuffle BOOLEAN,
    device TEXT
);
""")

conn.commit()
print("Tables created")

# Step 2: Load dim_artists
artists = pd.read_csv("dim_artists.csv")
for _, row in artists.iterrows():
    cur.execute("INSERT INTO dim_artists VALUES (%s, %s)", (row["artist_id"], row["artist_name"]))
conn.commit()
print(f"Loaded {len(artists)} artists")

# Step 3: Load dim_tracks
tracks = pd.read_csv("dim_tracks.csv")
for _, row in tracks.iterrows():
    cur.execute("""INSERT INTO dim_tracks VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                tuple(row))
conn.commit()
print(f"Loaded {len(tracks)} tracks")

# Step 4: Load dim_users
users = pd.read_csv("dim_users.csv")
for _, row in users.iterrows():
    cur.execute("INSERT INTO dim_users VALUES (%s,%s,%s,%s,%s,%s)",
                (row["user_id"], row["username"], row["country"], row["plan"], row["age_group"], row["signup_date"]))
conn.commit()
print(f"Loaded {len(users)} users")

# Step 5: Generate and load dim_dates
streams = pd.read_csv("fact_streams.csv", parse_dates=["timestamp"])
unique_dates = streams["timestamp"].dt.date.unique()
unique_dates.sort()

for i, d in enumerate(unique_dates):
    dt = pd.Timestamp(d)
    cur.execute("INSERT INTO dim_dates VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (i + 1, d, dt.year, dt.month, dt.day, dt.day_name(), dt.weekday() >= 5))
conn.commit()
print(f"Loaded {len(unique_dates)} dates")

# Build date lookup for fact_streams
date_lookup = {d: i + 1 for i, d in enumerate(unique_dates)}

# Step 6: Load track_genres
genres = pd.read_csv("track_genres.csv")
for _, row in genres.iterrows():
    cur.execute("INSERT INTO track_genres VALUES (%s, %s)", (row["track_id"], row["track_genre"]))
conn.commit()
print(f"Loaded {len(genres)} track-genre mappings")

# Step 7: Load fact_streams
print("Loading 500,000 streams (this takes a minute)...")
batch = []
for _, row in streams.iterrows():
    event_date = row["timestamp"].date()
    date_id = date_lookup.get(event_date, 1)
    batch.append((row["stream_id"], row["user_id"], row["track_id"], date_id,
                  row["timestamp"], row["listen_duration_ms"], row["skipped"],
                  row["shuffle"], row["device"]))

    if len(batch) >= 5000:
        cur.executemany("""INSERT INTO fact_streams VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", batch)
        conn.commit()
        batch = []

if batch:
    cur.executemany("""INSERT INTO fact_streams VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", batch)
    conn.commit()

print(f"Loaded {len(streams)} streams")

# Verify
cur.execute("SELECT COUNT(*) FROM fact_streams")
print(f"\nVerification - fact_streams rows: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM dim_tracks")
print(f"Verification - dim_tracks rows: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM dim_users")
print(f"Verification - dim_users rows: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\nDone! All data loaded into PostgreSQL.")