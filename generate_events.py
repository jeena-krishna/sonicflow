import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# Load our clean tracks
dim_tracks = pd.read_csv("dim_tracks.csv")
print(f"Loaded {len(dim_tracks)} tracks")

# Step 1: Generate fake users
NUM_USERS = 5000

countries = ["US", "UK", "India", "Brazil", "Germany", "Japan", "Mexico", "Canada", "France", "Australia"]
country_weights = [0.30, 0.12, 0.15, 0.10, 0.08, 0.07, 0.05, 0.05, 0.04, 0.04]

plans = ["free", "premium"]
plan_weights = [0.6, 0.4]

devices = ["mobile", "desktop", "tablet", "smart_speaker"]
device_weights = [0.55, 0.25, 0.12, 0.08]

dim_users = pd.DataFrame({
    "user_id": range(1, NUM_USERS + 1),
    "username": [f"user_{i}" for i in range(1, NUM_USERS + 1)],
    "country": np.random.choice(countries, NUM_USERS, p=country_weights),
    "plan": np.random.choice(plans, NUM_USERS, p=plan_weights),
    "age_group": np.random.choice(["13-17", "18-24", "25-34", "35-44", "45+"], NUM_USERS, p=[0.08, 0.30, 0.35, 0.17, 0.10]),
    "signup_date": [datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 730)) for _ in range(NUM_USERS)]
})

dim_users.to_csv("dim_users.csv", index=False)
print(f"Generated {NUM_USERS} users")

# Step 2: Generate streaming events
NUM_EVENTS = 500000

# Popular tracks get more streams (realistic distribution)
track_probs = dim_tracks["popularity"].values + 1  # +1 so 0-popularity tracks still get some plays
track_probs = track_probs / track_probs.sum()

# Generate events
print("Generating 500,000 streaming events...")

# Random timestamps over 6 months
start_date = datetime(2024, 1, 1)
random_days = np.random.randint(0, 180, NUM_EVENTS)
hour_weights = [
    0.01, 0.005, 0.005, 0.005, 0.005, 0.01,
    0.02, 0.04, 0.05, 0.05, 0.05, 0.05,
    0.05, 0.05, 0.05, 0.05, 0.05, 0.06,
    0.07, 0.08, 0.08, 0.07, 0.05, 0.03
]
hour_weights = [w / sum(hour_weights) for w in hour_weights]
random_hours = np.random.choice(24, NUM_EVENTS, p=hour_weights)
random_minutes = np.random.randint(0, 60, NUM_EVENTS)

timestamps = [start_date + timedelta(days=int(d), hours=int(h), minutes=int(m))
              for d, h, m in zip(random_days, random_hours, random_minutes)]

# Pick tracks (popular tracks get picked more)
track_indices = np.random.choice(len(dim_tracks), NUM_EVENTS, p=track_probs)
track_ids = dim_tracks.iloc[track_indices]["track_id"].values
track_durations = dim_tracks.iloc[track_indices]["duration_ms"].values

# Listen duration (realistic: some skip early, some listen fully, some replay)
listen_pct = np.random.beta(2, 1.5, NUM_EVENTS)  # skewed toward listening more
listen_duration_ms = (track_durations * listen_pct).astype(int)
skipped = listen_pct < 0.25  # skipped if listened less than 25%

events = pd.DataFrame({
    "stream_id": range(1, NUM_EVENTS + 1),
    "user_id": np.random.randint(1, NUM_USERS + 1, NUM_EVENTS),
    "track_id": track_ids,
    "timestamp": timestamps,
    "listen_duration_ms": listen_duration_ms,
    "skipped": skipped,
    "shuffle": np.random.choice([True, False], NUM_EVENTS, p=[0.4, 0.6]),
    "device": np.random.choice(devices, NUM_EVENTS, p=device_weights)
})

events.to_csv("fact_streams.csv", index=False)
print(f"Generated {NUM_EVENTS} streaming events")

# Quick stats
print(f"\nSkip rate: {skipped.mean()*100:.1f}%")
print(f"Avg listen: {listen_duration_ms.mean()/1000:.0f} seconds")
print(f"Date range: {min(timestamps).date()} to {max(timestamps).date()}")
print(f"Events per user (avg): {NUM_EVENTS/NUM_USERS:.0f}")