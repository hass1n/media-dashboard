import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

query = """
SELECT 
    SUM(COALESCE(mk.youtube_views, 0) + COALESCE(mk.source_youtube_views, 0) + COALESCE(pk_sum.p_views, 0)) as total_views
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
LEFT JOIN (
    SELECT mp.media_id, SUM(pk.part_youtube_views) as p_views
    FROM media_parts mp
    JOIN parts_kpis pk ON mp.part_id = pk.part_id
    GROUP BY mp.media_id
) pk_sum ON mo.media_id = pk_sum.media_id
WHERE mo.media_date >= '2025-05-13'
"""

result = pd.read_sql(query, engine)
print(f"Total YouTube Views (Last Year): {result.iloc[0,0]}")
