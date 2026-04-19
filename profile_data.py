import pandas as pd

# Load the dataset
df = pd.read_csv("dataset.csv")

# Basic info
print("=" * 50)
print("BASIC INFO")
print("=" * 50)
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print(f"Column names: {list(df.columns)}")

# Check for nulls
print("\n" + "=" * 50)
print("NULL VALUES")
print("=" * 50)
for col in df.columns:
    nulls = df[col].isnull().sum()
    if nulls > 0:
        print(f"  {col}: {nulls} nulls ({nulls/len(df)*100:.2f}%)")

# Check for duplicates
print("\n" + "=" * 50)
print("DUPLICATES")
print("=" * 50)
print(f"Duplicate track_ids: {df['track_id'].duplicated().sum()}")
print(f"Fully duplicate rows: {df.duplicated().sum()}")

# Show some duplicate track_ids to understand why
dupes = df[df['track_id'].duplicated(keep=False)].sort_values('track_id')
print(f"\nExample duplicate track_id:")
sample_id = dupes['track_id'].iloc[0]
print(dupes[dupes['track_id'] == sample_id][['track_id', 'track_name', 'artists', 'track_genre']].to_string())

# Check data types and unique values
print("\n" + "=" * 50)
print("COLUMN DETAILS")
print("=" * 50)
for col in df.columns:
    print(f"  {col:25s} | type: {str(df[col].dtype):10s} | unique: {df[col].nunique()}")

# Check for weird values
print("\n" + "=" * 50)
print("DATA QUALITY CHECKS")
print("=" * 50)
print(f"Tracks under 10 seconds: {(df['duration_ms'] < 10000).sum()}")
print(f"Tracks over 30 minutes: {(df['duration_ms'] > 1800000).sum()}")
print(f"Tracks with 0 popularity: {(df['popularity'] == 0).sum()}")
print(f"Multi-artist tracks (semicolon): {df['artists'].str.contains(';', na=False).sum()}")
print(f"Total genres: {df['track_genre'].nunique()}")
print(f"Tracks per genre: {df['track_genre'].value_counts().unique()}")