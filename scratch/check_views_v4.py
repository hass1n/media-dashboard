import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

# 1. Total Views in media_kpis (excluding joined media_output date range)
mk = pd.read_sql("SELECT * FROM media_kpis", engine)
pk = pd.read_sql("SELECT * FROM parts_kpis", engine)

total_youtube_views = (
    mk['youtube_views'].fillna(0) + 
    mk['source_youtube_views'].fillna(0)
).sum() + pk['part_youtube_views'].fillna(0).sum()

print(f"Grand Total YouTube Views in DB: {total_youtube_views}")

# 2. Get views by date
query = """
SELECT 
    mo.media_date,
    SUM(COALESCE(mk.youtube_views, 0) + COALESCE(mk.source_youtube_views, 0)) as m_views,
    SUM(COALESCE(pk_sum.p_views, 0)) as p_views
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
LEFT JOIN (
    SELECT mp.media_id, SUM(pk.part_youtube_views) as p_views
    FROM media_parts mp
    JOIN parts_kpis pk ON mp.part_id = pk.part_id
    GROUP BY mp.media_id
) pk_sum ON mo.media_id = pk_sum.media_id
GROUP BY mo.media_date
ORDER BY mo.media_date DESC
"""

df_dated = pd.read_sql(query, engine)
print("\nRecent YouTube Views by Date:")
print(df_dated.head(10))

# 3. Sum for 2026 specifically (since the user might mean 'this year so far')
sum_2026 = df_dated[df_dated['media_date'] >= pd.to_datetime('2026-01-01').date()]['m_views'].sum() + \
           df_dated[df_dated['media_date'] >= pd.to_datetime('2026-01-01').date()]['p_views'].sum()
print(f"\nSum for 2026: {sum_2026}")

# 4. Sum for 2025 specifically
sum_2025 = df_dated[(df_dated['media_date'] >= pd.to_datetime('2025-01-01').date()) & 
                    (df_dated['media_date'] < pd.to_datetime('2026-01-01').date())]['m_views'].sum() + \
           df_dated[(df_dated['media_date'] >= pd.to_datetime('2025-01-01').date()) & 
                    (df_dated['media_date'] < pd.to_datetime('2026-01-01').date())]['p_views'].sum()
print(f"Sum for 2025: {sum_2025}")
