import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

query = """
SELECT 
    mo.media_id,
    COALESCE(mk.youtube_views, 0) + COALESCE(mk.source_youtube_views, 0) as views,
    COALESCE(mk.youtube_likes, 0) + COALESCE(mk.source_youtube_likes, 0) as likes,
    COALESCE(mk.youtube_comments, 0) + COALESCE(mk.source_youtube_comments, 0) as comments,
    COALESCE(mk.youtube_shares, 0) as shares,
    COALESCE(mk.youtube_card_clicks, 0) as clicks,
    COALESCE(pk_sum.p_views, 0) as p_views,
    COALESCE(pk_sum.p_likes, 0) as p_likes,
    COALESCE(pk_sum.p_comments, 0) as p_comments,
    COALESCE(pk_sum.p_shares, 0) as p_shares,
    COALESCE(pk_sum.p_clicks, 0) as p_clicks
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
total_views = (df['views'] + df['p_views']).sum()
total_likes = (df['likes'] + df['p_likes']).sum()
total_others = (df['comments'] + df['p_comments'] + df['shares'] + df['p_shares'] + df['clicks'] + df['p_clicks']).sum()

print(f"Views: {total_views}")
print(f"Likes: {total_likes}")
print(f"Others: {total_others}")
print(f"Views + Likes: {total_views + total_likes}")
print(f"Views + Likes + Others: {total_views + total_likes + total_others}")
