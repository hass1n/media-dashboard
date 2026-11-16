import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

query = """
SELECT 
    mo.media_id,
    mk.*,
    pk_sum.*
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
LEFT JOIN (
    SELECT mp.media_id, 
           SUM(pk.part_youtube_views) as p_views, 
           SUM(pk.part_youtube_likes) as p_likes,
           SUM(pk.part_youtube_comments) as p_comments,
           SUM(pk.part_youtube_shares) as p_shares,
           SUM(pk.part_youtube_card_clicks) as p_clicks
    FROM media_parts mp
    JOIN parts_kpis pk ON mp.part_id = pk.part_id
    GROUP BY mp.media_id
) pk_sum ON mo.media_id = pk_sum.media_id
WHERE mo.media_date >= '2025-05-13'
"""

df = pd.read_sql(query, engine)
y_cols = [c for c in df.columns if 'youtube' in c.lower() and 'watch' not in c.lower() and 'date' not in c.lower() and 'link' not in c.lower()]
print(f"YouTube Columns found: {y_cols}")

total_sum = 0
for col in y_cols:
    total_sum += pd.to_numeric(df[col], errors='coerce').fillna(0).sum()

print(f"Sum of all YouTube metrics: {total_sum}")
