import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

query = """
SELECT 
    mo.media_date,
    SUM(COALESCE(mk.youtube_views, 0) + COALESCE(mk.source_youtube_views, 0) + COALESCE(pk_sum.p_views, 0)) as total_v
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
LEFT JOIN (
    SELECT mp.media_id, SUM(pk.part_youtube_views) as p_views
    FROM media_parts mp
    JOIN parts_kpis pk ON mp.part_id = pk.part_id
    GROUP BY mp.media_id
) pk_sum ON mo.media_id = pk_sum.media_id
GROUP BY mo.media_date
"""

df = pd.read_sql(query, engine)
df['media_date'] = pd.to_datetime(df['media_date'])
df = df.sort_values('media_date')

# Try different "last year" ranges
ranges = [
    ('2025-05-13', '2026-05-13'), # Last 12 months
    ('2025-01-01', '2025-12-31'), # Full year 2025
    ('2026-01-01', '2026-05-13'), # 2026 to date
    ('2024-05-13', '2025-05-13'), # Previous 12 months
]

for start, end in ranges:
    s = df[(df['media_date'] >= start) & (df['media_date'] <= end)]['total_v'].sum()
    print(f"{start} to {end}: {s}")
