import pandas as pd

# Load raw data
df = pd.read_csv("dataset.csv")
print(f"Raw data: {len(df)} rows")

# Step 1: Drop useless column
df = df.drop(columns=["Unnamed: 0"])
print("Dropped 'Unnamed: 0' column")

# Step 2: Handle nulls - drop rows where key fields are null
before = len(df)
df = df.dropna(subset=["track_id", "artists", "track_name"])
print(f"Dropped {before - len(df)} rows with null track_id/artists/track_name")

# Step 3: Build track-genre mapping (before deduplication!)
# A track can belong to multiple genres
track_genres = df[["track_id", "track_genre"]].drop_duplicates()
track_genres.to_csv("track_genres.csv", index=False)
print(f"Track-genre mapping: {len(track_genres)} rows ({track_genres['track_id'].nunique()} unique tracks)")

# Step 4: Deduplicate tracks - keep first occurrence
before = len(df)
df = df.drop_duplicates(subset=["track_id"], keep="first")
print(f"Deduplicated: {before} -> {len(df)} rows (removed {before - len(df)} duplicates)")

# Step 5: Split multi-artists and build dim_artists
all_artists = set()
for artists_str in df["artists"].dropna():
    for artist in artists_str.split(";"):
        all_artists.add(artist.strip())

dim_artists = pd.DataFrame({
    "artist_id": range(1, len(all_artists) + 1),
    "artist_name": sorted(all_artists)
})
dim_artists.to_csv("dim_artists.csv", index=False)
print(f"dim_artists: {len(dim_artists)} unique artists")

# Step 6: Build dim_tracks (clean, one row per track)
dim_tracks = df[["track_id", "track_name", "album_name", "artists", "popularity",
                  "duration_ms", "explicit", "danceability", "energy", "key",
                  "loudness", "mode", "speechiness", "acousticness",
                  "instrumentalness", "liveness", "valence", "tempo",
                  "time_signature"]].copy()
dim_tracks.to_csv("dim_tracks.csv", index=False)
print(f"dim_tracks: {len(dim_tracks)} tracks")

# Summary
print("\n" + "=" * 50)
print("FILES CREATED:")
print("  dim_tracks.csv    - one row per track")
print("  dim_artists.csv   - one row per artist")
print("  track_genres.csv  - track to genre mapping")
print("=" * 50)