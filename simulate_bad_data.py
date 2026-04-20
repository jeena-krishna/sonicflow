import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    port="5433",
    database="sonicflow",
    user="jeena",
    password="sonicflow123"
)
cur = conn.cursor()

# First, drop the foreign key constraint so we can inject bad data
print("Dropping foreign key constraints...")
cur.execute("ALTER TABLE fact_streams DROP CONSTRAINT IF EXISTS fact_streams_track_id_fkey")
cur.execute("ALTER TABLE fact_streams DROP CONSTRAINT IF EXISTS fact_streams_user_id_fkey")
cur.execute("ALTER TABLE fact_streams DROP CONSTRAINT IF EXISTS fact_streams_date_id_fkey")
conn.commit()

# Problem 1: Insert streams with fake track_ids (orphan records)
print("Injecting 50 streams with fake track_ids...")
for i in range(50):
    cur.execute("""
        INSERT INTO fact_streams VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (600000 + i, 1, 'FAKE_TRACK_' + str(i), 1,
          '2024-06-15 12:00:00', 120000, False, False, 'mobile'))

# Problem 2: Set some track_ids to NULL
print("Setting 5000 track_ids to NULL...")
cur.execute("""
    UPDATE fact_streams SET track_id = NULL 
    WHERE stream_id BETWEEN 1 AND 5000
""")

conn.commit()
print("Bad data injected! Now run validate_data.py again.")
cur.close()
conn.close()