import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

query = """
SELECT 
    mo.media_id,
    mk.youtube_watch_time,
    pk.part_youtube_watch_time
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
LEFT JOIN media_parts mp ON mo.media_id = mp.media_id
LEFT JOIN parts_kpis pk ON mp.part_id = pk.part_id
WHERE mo.media_date >= '2025-05-13'
"""

df = pd.read_sql(query, engine)

def to_seconds(s):
    try:
        return pd.to_timedelta(s, errors='coerce').total_seconds()
    except:
        try:
             return float(s)
        except:
             return 0

w1 = df['youtube_watch_time'].apply(to_seconds).sum()
w2 = df['part_youtube_watch_time'].apply(to_seconds).sum()

print(f"Total Watch Time (seconds): {w1 + w2}")
print(f"Total Watch Time (minutes): {(w1 + w2) / 60}")
print(f"Total Watch Time (hours): {(w1 + w2) / 3600}")
