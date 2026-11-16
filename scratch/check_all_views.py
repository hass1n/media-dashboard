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
           SUM(pk.part_youtube_views) as p_y_views, 
           SUM(pk.part_facebook_views) as p_f_views,
           SUM(pk.part_twitter_views) as p_t_views,
           SUM(pk.part_tiktok_views) as p_tk_views,
           SUM(pk.part_website_views) as p_w_views,
           SUM(pk.part_instagram_plays) as p_i_plays
    FROM media_parts mp
    JOIN parts_kpis pk ON mp.part_id = pk.part_id
    GROUP BY mp.media_id
) pk_sum ON mo.media_id = pk_sum.media_id
WHERE mo.media_date >= '2025-05-13'
"""

df = pd.read_sql(query, engine)
print(f"Total Rows: {len(df)}")

v_cols = [c for c in df.columns if 'views' in c.lower() or 'plays' in c.lower()]
print(f"Views columns: {v_cols}")

for col in v_cols:
    s = pd.to_numeric(df[col], errors='coerce').fillna(0).sum()
    print(f"{col}: {s}")
