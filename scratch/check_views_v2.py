import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

query = """
SELECT 
    mo.media_id,
    COALESCE(mk.youtube_views, 0) as v1,
    COALESCE(mk.source_youtube_views, 0) as v2,
    COALESCE(pk_sum.p_views, 0) as v3,
    COALESCE(mk.youtube_likes, 0) as l1,
    COALESCE(mk.source_youtube_likes, 0) as l2,
    COALESCE(pk_sum.p_likes, 0) as l3
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
LEFT JOIN (
    SELECT mp.media_id, SUM(pk.part_youtube_views) as p_views, SUM(pk.part_youtube_likes) as p_likes
    FROM media_parts mp
    JOIN parts_kpis pk ON mp.part_id = pk.part_id
    GROUP BY mp.media_id
) pk_sum ON mo.media_id = pk_sum.media_id
WHERE mo.media_date >= '2025-05-13'
"""

df = pd.read_sql(query, engine)
total_views = (df['v1'] + df['v2'] + df['v3']).sum()
total_likes = (df['l1'] + df['l2'] + df['l3']).sum()
total_eng = total_views + total_likes

print(f"Total YouTube Views: {total_views}")
print(f"Total YouTube Likes: {total_likes}")
print(f"Total YouTube Engagements (Views + Likes): {total_eng}")
