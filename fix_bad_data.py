import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    port="5433",
    database="sonicflow",
    user="jeena",
    password="sonicflow123"
)
cur = conn.cursor()

# Remove fake streams
cur.execute("DELETE FROM fact_streams WHERE stream_id >= 600000")
print(f"Deleted fake streams")

# Restore NULL track_ids from our CSV
import pandas as pd
streams = pd.read_csv("fact_streams.csv")
for _, row in streams[streams.stream_id.between(1, 5000)].iterrows():
    cur.execute("UPDATE fact_streams SET track_id = %s WHERE stream_id = %s",
                (row['track_id'], row['stream_id']))

conn.commit()
print("Restored NULL track_ids")

# Re-add foreign key constraints
cur.execute("""ALTER TABLE fact_streams 
    ADD CONSTRAINT fact_streams_track_id_fkey 
    FOREIGN KEY (track_id) REFERENCES dim_tracks(track_id)""")
cur.execute("""ALTER TABLE fact_streams 
    ADD CONSTRAINT fact_streams_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES dim_users(user_id)""")
conn.commit()
print("Restored foreign key constraints")

cur.close()
conn.close()
print("Database cleaned!")