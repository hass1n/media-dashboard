import pandas as pd
from sqlalchemy import create_engine
from app import get_unified_media_df, get_db_connection

# Re-create engine as in app.py
from app import engine

start_date = '2020-02-01'
end_date = '2026-06-01'

df = get_unified_media_df(start_date, end_date)

valid_media_ids = df['media_id'].unique().tolist()
with engine.connect() as conn:
    mk_raw = pd.read_sql("SELECT * FROM media_kpis WHERE media_id IN %(ids)s", conn, params={'ids': tuple(valid_media_ids) if valid_media_ids else (0,)})
    pk_raw = pd.read_sql("""
        SELECT pk.* 
        FROM parts_kpis pk
        JOIN media_parts mp ON pk.part_id = mp.part_id
        WHERE mp.media_id IN %(ids)s
    """, conn, params={'ids': tuple(valid_media_ids) if valid_media_ids else (0,)})

platforms = ['facebook', 'youtube', 'twitter', 'tiktok', 'instagram', 'website']

def get_platform_metrics_from_df(df_raw, platform_name, prefix=''):
    stats = {'views': 0, 'eng': 0}
    v_cols = [c for c in df_raw.columns if platform_name in c and ('views' in c.lower() or 'plays' in c.lower())]
    l_cols = [c for c in df_raw.columns if platform_name in c and 'likes' in c.lower()]
    if not l_cols:
        l_cols = [c for c in df_raw.columns if platform_name in c and ('eng' in c.lower() or 'event' in c.lower()) and 'views' not in c.lower() and 'plays' not in c.lower()]

    def sum_with_numeric(cols_to_sum, dframe):
        total = 0
        for col in cols_to_sum:
            s = dframe[col]
            if 'duration' in col.lower() or 'watch_time' in col.lower():
                try:
                    total += pd.to_timedelta(s, errors='coerce').dt.total_seconds().fillna(0).sum()
                except:
                    total += pd.to_numeric(s, errors='coerce').fillna(0).sum()
            else:
                total += pd.to_numeric(s, errors='coerce').fillna(0).sum()
        return total

    stats['views'] = sum_with_numeric(v_cols, df_raw)
    likes_total = sum_with_numeric(l_cols, df_raw)
    stats['eng'] = stats['views'] + likes_total
    return stats

print("From pandas-based logic:")
for platform in platforms:
    mk_p = get_platform_metrics_from_df(mk_raw, platform)
    pk_p = get_platform_metrics_from_df(pk_raw, platform, prefix='part_')
    print(f"{platform}: views: {mk_p['views'] + pk_p['views']}, eng: {mk_p['eng'] + pk_p['eng']}")
