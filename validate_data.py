import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import json

conn = psycopg2.connect(
    host="127.0.0.1",
    port="5433",
    database="sonicflow",
    user="jeena",
    password="sonicflow123"
)
cur = conn.cursor()

results = []

def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"check": name, "status": status, "detail": detail})
    icon = "✓" if passed else "✗"
    print(f"  {icon} {name}: {status} {detail}")

print("=" * 60)
print("SONICFLOW DATA VALIDATION REPORT")
print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 1. SCHEMA VALIDATION
print("\n[1] SCHEMA VALIDATION")

expected_columns = {
    "fact_streams": ["stream_id", "user_id", "track_id", "date_id", "timestamp", 
                     "listen_duration_ms", "skipped", "shuffle", "device"],
    "dim_tracks": ["track_id", "track_name", "album_name", "artists", "popularity",
                   "duration_ms", "explicit", "danceability", "energy", "key",
                   "loudness", "mode", "speechiness", "acousticness", 
                   "instrumentalness", "liveness", "valence", "tempo", "time_signature"],
    "dim_users": ["user_id", "username", "country", "plan", "age_group", "signup_date"]
}

for table, expected in expected_columns.items():
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = '{table}' ORDER BY ordinal_position
    """)
    actual = [row[0] for row in cur.fetchall()]
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)
    passed = len(missing) == 0
    detail = f"missing: {missing}" if missing else "all columns present"
    check(f"{table} schema", passed, detail)

# 2. VOLUME CHECKS
print("\n[2] VOLUME CHECKS")

volume_expectations = {
    "fact_streams": {"min": 100000, "max": 1000000},
    "dim_tracks": {"min": 50000, "max": 200000},
    "dim_users": {"min": 1000, "max": 50000}
}

for table, bounds in volume_expectations.items():
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    passed = bounds["min"] <= count <= bounds["max"]
    check(f"{table} volume", passed, f"{count} rows (expected {bounds['min']}-{bounds['max']})")

# 3. NULL RATE MONITORING
print("\n[3] NULL RATE CHECKS")

critical_columns = {
    "fact_streams": ["stream_id", "user_id", "track_id", "timestamp"],
    "dim_tracks": ["track_id", "track_name"],
    "dim_users": ["user_id", "country"]
}

for table, columns in critical_columns.items():
    for col in columns:
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
        null_count = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        total = cur.fetchone()[0]
        null_pct = (null_count / total * 100) if total > 0 else 0
        passed = null_pct < 1.0  # less than 1% nulls is acceptable
        check(f"{table}.{col} nulls", passed, f"{null_count} nulls ({null_pct:.2f}%)")

# 4. FRESHNESS CHECK
print("\n[4] FRESHNESS CHECK")

cur.execute("SELECT MAX(timestamp) FROM fact_streams")
latest = cur.fetchone()[0]
check("data freshness", latest is not None, f"latest event: {latest}")

# 5. REFERENTIAL INTEGRITY
print("\n[5] REFERENTIAL INTEGRITY")

# Check: every track_id in streams exists in tracks
cur.execute("""
    SELECT COUNT(DISTINCT f.track_id) 
    FROM fact_streams f 
    LEFT JOIN dim_tracks t ON f.track_id = t.track_id 
    WHERE t.track_id IS NULL
""")
orphan_tracks = cur.fetchone()[0]
check("streams→tracks integrity", orphan_tracks == 0, 
      f"{orphan_tracks} orphan track_ids")

# Check: every user_id in streams exists in users
cur.execute("""
    SELECT COUNT(DISTINCT f.user_id) 
    FROM fact_streams f 
    LEFT JOIN dim_users u ON f.user_id = u.user_id 
    WHERE u.user_id IS NULL
""")
orphan_users = cur.fetchone()[0]
check("streams→users integrity", orphan_users == 0, 
      f"{orphan_users} orphan user_ids")

# 6. STATISTICAL ANOMALY DETECTION
print("\n[6] STATISTICAL ANOMALY DETECTION")

# Check if average listen duration is within reasonable range
cur.execute("SELECT AVG(listen_duration_ms) FROM fact_streams")
avg_listen = cur.fetchone()[0]
passed = 30000 < avg_listen < 300000  # between 30 sec and 5 min
check("avg listen duration", passed, f"{avg_listen/1000:.0f} seconds")

# Check if skip rate is reasonable
cur.execute("""
    SELECT 100.0 * SUM(CASE WHEN skipped THEN 1 ELSE 0 END) / COUNT(*) 
    FROM fact_streams
""")
skip_rate = cur.fetchone()[0]
passed = 5 < skip_rate < 50  # between 5% and 50%
check("skip rate", passed, f"{skip_rate:.1f}%")

# Check streams per user distribution
cur.execute("""
    SELECT STDDEV(cnt) / AVG(cnt) as cv FROM (
        SELECT user_id, COUNT(*) as cnt FROM fact_streams GROUP BY user_id
    ) t
""")
cv = cur.fetchone()[0]
passed = cv < 1.0  # coefficient of variation under 1 means no extreme outliers
check("streams per user distribution", passed, f"CV={cv:.3f}")

# SUMMARY
print("\n" + "=" * 60)
passed_count = sum(1 for r in results if r["status"] == "PASS")
failed_count = sum(1 for r in results if r["status"] == "FAIL")
print(f"TOTAL: {passed_count} passed, {failed_count} failed out of {len(results)} checks")

if failed_count > 0:
    print("\nFAILED CHECKS:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  ✗ {r['check']}: {r['detail']}")
print("=" * 60)

# Save results
with open("validation_results.json", "w") as f:
    json.dump({
        "run_time": datetime.now().isoformat(),
        "total_checks": len(results),
        "passed": passed_count,
        "failed": failed_count,
        "results": results
    }, f, indent=2)
print("\nResults saved to validation_results.json")

cur.close()
conn.close()