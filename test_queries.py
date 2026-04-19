import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    port="5433",
    database="sonicflow",
    user="jeena",
    password="sonicflow123"
)
cur = conn.cursor()

# Query 1: Top 10 most streamed tracks
print("=" * 60)
print("TOP 10 MOST STREAMED TRACKS")
print("=" * 60)
cur.execute("""
    SELECT t.track_name, t.artists, COUNT(*) as stream_count
    FROM fact_streams f
    JOIN dim_tracks t ON f.track_id = t.track_id
    GROUP BY t.track_name, t.artists
    ORDER BY stream_count DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0]:40s} | {row[1]:30s} | {row[2]} streams")

# Query 2: Streams by country
print("\n" + "=" * 60)
print("STREAMS BY COUNTRY")
print("=" * 60)
cur.execute("""
    SELECT u.country, COUNT(*) as streams, 
           ROUND(AVG(f.listen_duration_ms)/1000.0, 1) as avg_listen_sec
    FROM fact_streams f
    JOIN dim_users u ON f.user_id = u.user_id
    GROUP BY u.country
    ORDER BY streams DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:15s} | {row[1]:>8} streams | avg listen: {row[2]}s")

# Query 3: Skip rate by device
print("\n" + "=" * 60)
print("SKIP RATE BY DEVICE")
print("=" * 60)
cur.execute("""
    SELECT f.device, 
           COUNT(*) as total,
           ROUND(100.0 * SUM(CASE WHEN f.skipped THEN 1 ELSE 0 END) / COUNT(*), 1) as skip_pct
    FROM fact_streams f
    GROUP BY f.device
    ORDER BY skip_pct DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:15s} | {row[1]:>8} streams | skip rate: {row[2]}%")

# Query 4: Peak listening hours
print("\n" + "=" * 60)
print("STREAMS BY HOUR OF DAY")
print("=" * 60)
cur.execute("""
    SELECT EXTRACT(HOUR FROM f.timestamp)::int as hour, COUNT(*) as streams
    FROM fact_streams f
    GROUP BY hour
    ORDER BY hour
""")
for row in cur.fetchall():
    bar = "█" * (row[1] // 1000)
    print(f"  {row[0]:2d}:00 | {row[1]:>6} | {bar}")

cur.close()
conn.close()