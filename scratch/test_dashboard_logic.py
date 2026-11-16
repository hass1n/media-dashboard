import app

df = app.get_unified_media_df('2025-01-01', '2025-12-31')
valid_media_ids = df['media_id'].unique().tolist()

import psycopg2
import pandas as pd
conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

if valid_media_ids:
    mk_raw = pd.read_sql("SELECT * FROM media_kpis WHERE media_id IN %(ids)s", conn, params={'ids': tuple(valid_media_ids)})
    pk_raw = pd.read_sql("""
        SELECT pk.* 
        FROM parts_kpis pk
        JOIN media_parts mp ON pk.part_id = mp.part_id
        WHERE mp.media_id IN %(ids)s
    """, conn, params={'ids': tuple(valid_media_ids)})
else:
    print("No valid media IDs")
    exit()

stats = app.get_platform_metrics_from_df(mk_raw, 'youtube')
stats_p = app.get_platform_metrics_from_df(pk_raw, 'youtube', prefix='part_')

total_views = stats['views'] + stats_p['views']
print(f"2025 Total YouTube Views (from dashboard logic): {total_views}")

# Now for all time
df_all = app.get_unified_media_df('2020-02-01', '2026-06-01')
all_ids = df_all['media_id'].unique().tolist()
mk_all = pd.read_sql("SELECT * FROM media_kpis WHERE media_id IN %(ids)s", conn, params={'ids': tuple(all_ids)})
pk_all = pd.read_sql("""
    SELECT pk.* 
    FROM parts_kpis pk
    JOIN media_parts mp ON pk.part_id = mp.part_id
    WHERE mp.media_id IN %(ids)s
""", conn, params={'ids': tuple(all_ids)})

stats_all = app.get_platform_metrics_from_df(mk_all, 'youtube')
stats_p_all = app.get_platform_metrics_from_df(pk_all, 'youtube', prefix='part_')
total_views_all = stats_all['views'] + stats_p_all['views']
print(f"All Time Total YouTube Views (from dashboard logic): {total_views_all}")

# Print mk_raw 'views' calculation components
v_cols = [c for c in mk_all.columns if 'youtube' in c and ('views' in c.lower() or 'plays' in c.lower())]
print(f"\nmk_all views columns: {v_cols}")
for c in v_cols:
    print(f"  {c}: {pd.to_numeric(mk_all[c], errors='coerce').fillna(0).sum()}")

pv_cols = [c for c in pk_all.columns if 'youtube' in c and ('views' in c.lower() or 'plays' in c.lower())]
print(f"\npk_all views columns: {pv_cols}")
for c in pv_cols:
    print(f"  {c}: {pd.to_numeric(pk_all[c], errors='coerce').fillna(0).sum()}")

conn.close()
