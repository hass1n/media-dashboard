"""
Debug: Compare January 2026 totals between PHP (show_all.php) and Python (app.py)
Run this from the media_db folder:  python scratch/debug_jan2026.py
"""
import psycopg2
import pandas as pd

START = '2026-01-01'
END   = '2026-01-31'

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

# ─────────────────────────────────────────────────────────────────
# METHOD 1 — PHP way
# Only media_output rows, KPIs from media_kpis per row.
# Parts from parts_kpis (all parts, no program filter).
# Conditionally count FB/YT engagements only when views exist.
# ─────────────────────────────────────────────────────────────────
print("=" * 60)
print("METHOD 1 — PHP show_all.php way")
print("=" * 60)

# --- Main output rows ---
main_sql = """
SELECT mo.media_id,
       mk.website_views,
       mk.website_event_count,
       mk.source_youtube_views,
       mk.source_youtube_likes,
       mk.source_youtube_comments,
       mk.youtube_views,
       mk.youtube_likes,
       mk.youtube_comments,
       mk.youtube_shares,
       mk.youtube_card_clicks,
       mk.facebook_views,
       mk.facebook_comments,
       mk.facebook_shares,
       mk.facebook_likes,
       mk.facebook_love,
       mk.facebook_haha,
       mk.facebook_wow,
       mk.facebook_sad,
       mk.facebook_angry,
       mk.facebook_link_clicks,
       mk.instagram_plays,
       mk.instagram_engagements,
       mk.twitter_impressions,
       mk.twitter_total_engagement,
       mk.tiktok_views,
       mk.tiktok_engagements
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
WHERE mo.media_date BETWEEN %s AND %s
"""
main_df = pd.read_sql_query(main_sql, conn, params=(START, END))

def n(v):
    """Coerce scalar to numeric, None/NaN → 0"""
    try:
        val = float(v)
        return 0.0 if val != val else val  # NaN check
    except (TypeError, ValueError):
        return 0.0

php_total_views       = 0
php_total_engagements = 0

for _, r in main_df.iterrows():
    # Views (PHP accumulates unconditionally)
    php_total_views += n(r['website_views'])
    php_total_views += n(r['source_youtube_views'])
    php_total_views += n(r['youtube_views'])
    php_total_views += n(r['facebook_views'])
    php_total_views += n(r['instagram_plays'])
    php_total_views += n(r['twitter_impressions'])
    php_total_views += n(r['tiktok_views'])

    # Engagements (PHP is conditional on views existing)
    php_total_engagements += n(r['website_event_count'])
    php_total_engagements += n(r['source_youtube_likes']) + n(r['source_youtube_comments'])
    if n(r['youtube_views']) > 0:
        yt_eng = n(r['youtube_likes']) + n(r['youtube_comments']) + n(r['youtube_shares']) + n(r['youtube_card_clicks'])
        php_total_engagements += yt_eng
    if n(r['facebook_views']) > 0:
        fb_eng = (n(r['facebook_comments']) + n(r['facebook_shares']) + n(r['facebook_likes']) +
                  n(r['facebook_love']) + n(r['facebook_haha']) + n(r['facebook_wow']) +
                  n(r['facebook_sad']) + n(r['facebook_angry']) + n(r['facebook_link_clicks']))
        php_total_engagements += fb_eng
    php_total_engagements += n(r['instagram_engagements'])
    php_total_engagements += n(r['twitter_total_engagement'])
    php_total_engagements += n(r['tiktok_engagements'])

print(f"  Main output rows: {len(main_df)}")
print(f"  Views after main rows:       {int(php_total_views):,}")
print(f"  Engagements after main rows: {int(php_total_engagements):,}")

# --- Parts rows (PHP only includes parts for TV/Radio interviews) ---
parts_sql = """
SELECT mp.part_id,
       pk.part_website_views,
       pk.part_website_event_count,
       pk.part_youtube_views,
       pk.part_youtube_likes,
       pk.part_youtube_comments,
       pk.part_youtube_shares,
       pk.part_youtube_card_clicks,
       pk.part_facebook_views,
       pk.part_facebook_comments,
       pk.part_facebook_shares,
       pk.part_facebook_likes,
       pk.part_facebook_love,
       pk.part_facebook_haha,
       pk.part_facebook_wow,
       pk.part_facebook_sad,
       pk.part_facebook_angry,
       pk.part_facebook_link_clicks,
       pk.part_instagram_plays,
       pk.part_instagram_engagements,
       pk.part_twitter_impressions,
       pk.part_twitter_total_engagement,
       pk.part_tiktok_views,
       pk.part_tiktok_engagements
FROM media_parts mp
JOIN media_output mo ON mp.media_id = mo.media_id
LEFT JOIN parts_kpis pk ON mp.part_id = pk.part_id
WHERE mo.media_date BETWEEN %s AND %s
"""
parts_df = pd.read_sql_query(parts_sql, conn, params=(START, END))

for _, r in parts_df.iterrows():
    php_total_views += n(r['part_website_views'])
    php_total_views += n(r['part_youtube_views'])
    php_total_views += n(r['part_facebook_views'])
    php_total_views += n(r['part_instagram_plays'])
    php_total_views += n(r['part_twitter_impressions'])
    php_total_views += n(r['part_tiktok_views'])

    php_total_engagements += n(r['part_website_event_count'])
    if n(r['part_youtube_views']) > 0:
        php_total_engagements += (n(r['part_youtube_likes']) + n(r['part_youtube_comments']) +
                                   n(r['part_youtube_shares']) + n(r['part_youtube_card_clicks']))
    if n(r['part_facebook_views']) > 0:
        php_total_engagements += (n(r['part_facebook_comments']) + n(r['part_facebook_shares']) +
                                   n(r['part_facebook_likes']) + n(r['part_facebook_love']) +
                                   n(r['part_facebook_haha']) + n(r['part_facebook_wow']) +
                                   n(r['part_facebook_sad']) + n(r['part_facebook_angry']) +
                                   n(r['part_facebook_link_clicks']))
    php_total_engagements += n(r['part_instagram_engagements'])
    php_total_engagements += n(r['part_twitter_total_engagement'])
    php_total_engagements += n(r['part_tiktok_engagements'])

print(f"  Parts rows: {len(parts_df)}")
print(f"\n  ✅ PHP Total Views:       {int(php_total_views):,}")
print(f"  ✅ PHP Total Engagements: {int(php_total_engagements):,}")


# ─────────────────────────────────────────────────────────────────
# METHOD 2 — Python app.py way (UNION ALL, df_exploded by programs)
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("METHOD 2 — Python app.py (current) way")
print("=" * 60)

py_sql = """
SELECT
    mo.media_id::text AS media_id,
    mo.media_date AS date,
    (SELECT string_agg(media_program, ',') FROM media_programs WHERE media_id = mo.media_id) AS programs,
    mk.facebook_views,
    (COALESCE(mk.facebook_comments,0)+COALESCE(mk.facebook_shares,0)+COALESCE(mk.facebook_likes,0)+
     COALESCE(mk.facebook_love,0)+COALESCE(mk.facebook_haha,0)+COALESCE(mk.facebook_wow,0)+
     COALESCE(mk.facebook_sad,0)+COALESCE(mk.facebook_angry,0)+COALESCE(mk.facebook_link_clicks,0)) AS facebook_total_engagments,
    mk.youtube_views,
    mk.source_youtube_views,
    mk.source_youtube_likes,
    mk.source_youtube_comments,
    (COALESCE(mk.youtube_likes,0)+COALESCE(mk.youtube_comments,0)+
     COALESCE(mk.youtube_shares,0)+COALESCE(mk.youtube_card_clicks,0)) AS youtube_engagments,
    mk.website_views,
    mk.website_event_count AS website_engagments,
    mk.twitter_impressions,
    mk.twitter_total_engagement AS twitter_total_engagment,
    mk.tiktok_views,
    mk.tiktok_engagements AS tiktok_engagments,
    mk.instagram_plays AS insta_views,
    mk.instagram_engagements AS instagram_engagment
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
WHERE mo.media_date BETWEEN %s AND %s

UNION ALL

SELECT
    'p' || mp.part_id::text AS media_id,
    mo.media_date AS date,
    (SELECT string_agg(part_program_name, ',') FROM parts_programs WHERE part_id = mp.part_id) AS programs,
    pk.part_facebook_views AS facebook_views,
    (COALESCE(pk.part_facebook_comments,0)+COALESCE(pk.part_facebook_shares,0)+COALESCE(pk.part_facebook_likes,0)+
     COALESCE(pk.part_facebook_love,0)+COALESCE(pk.part_facebook_haha,0)+COALESCE(pk.part_facebook_wow,0)+
     COALESCE(pk.part_facebook_sad,0)+COALESCE(pk.part_facebook_angry,0)+COALESCE(pk.part_facebook_link_clicks,0)) AS facebook_total_engagments,
    pk.part_youtube_views AS youtube_views,
    0 AS source_youtube_views,
    0 AS source_youtube_likes,
    0 AS source_youtube_comments,
    (COALESCE(pk.part_youtube_likes,0)+COALESCE(pk.part_youtube_comments,0)+
     COALESCE(pk.part_youtube_shares,0)+COALESCE(pk.part_youtube_card_clicks,0)) AS youtube_engagments,
    pk.part_website_views AS website_views,
    pk.part_website_event_count AS website_engagments,
    pk.part_twitter_impressions AS twitter_impressions,
    pk.part_twitter_total_engagement AS twitter_total_engagment,
    pk.part_tiktok_views AS tiktok_views,
    pk.part_tiktok_engagements AS tiktok_engagments,
    pk.part_instagram_plays AS insta_views,
    pk.part_instagram_engagements AS instagram_engagment
FROM media_parts mp
JOIN media_output mo ON mp.media_id = mo.media_id
LEFT JOIN parts_kpis pk ON mp.part_id = pk.part_id
WHERE mo.media_date BETWEEN %s AND %s
"""
py_df = pd.read_sql_query(py_sql, conn, params=(START, END, START, END))

def s(df, col):
    if col not in df.columns: return 0
    return pd.to_numeric(df[col], errors='coerce').fillna(0).sum()

# BEFORE exploding by programs
py_views_no_explode = (s(py_df,'facebook_views') + s(py_df,'youtube_views') +
                        s(py_df,'source_youtube_views') + s(py_df,'insta_views') +
                        s(py_df,'twitter_impressions') + s(py_df,'tiktok_views') +
                        s(py_df,'website_views'))

py_eng_no_explode   = (s(py_df,'facebook_total_engagments') + s(py_df,'youtube_engagments') +
                        s(py_df,'source_youtube_likes') + s(py_df,'source_youtube_comments') +
                        s(py_df,'instagram_engagment') + s(py_df,'twitter_total_engagment') +
                        s(py_df,'tiktok_engagments') + s(py_df,'website_engagments'))

print(f"  Total rows (UNION): {len(py_df)}")
print(f"  ── Before program-explode:")
print(f"     Views:       {int(py_views_no_explode):,}")
print(f"     Engagements: {int(py_eng_no_explode):,}")

# AFTER exploding by programs (what the current index route does)
py_df_ex = py_df.copy()
py_df_ex['programs'] = py_df_ex['programs'].astype(str).str.split(',')
py_df_ex = py_df_ex.explode('programs')
py_df_ex['programs'] = py_df_ex['programs'].str.strip().str.upper()
py_df_ex = py_df_ex[py_df_ex['programs'] != '']
py_df_ex = py_df_ex.drop_duplicates(subset=['media_id', 'programs'])

py_views_exploded = (s(py_df_ex,'facebook_views') + s(py_df_ex,'youtube_views') +
                      s(py_df_ex,'source_youtube_views') + s(py_df_ex,'insta_views') +
                      s(py_df_ex,'twitter_impressions') + s(py_df_ex,'tiktok_views') +
                      s(py_df_ex,'website_views'))

py_eng_exploded   = (s(py_df_ex,'facebook_total_engagments') + s(py_df_ex,'youtube_engagments') +
                      s(py_df_ex,'source_youtube_likes') + s(py_df_ex,'source_youtube_comments') +
                      s(py_df_ex,'instagram_engagment') + s(py_df_ex,'twitter_total_engagment') +
                      s(py_df_ex,'tiktok_engagments') + s(py_df_ex,'website_engagments'))

print(f"  ── After program-explode (current app.py index behaviour):")
print(f"     Rows after explode:  {len(py_df_ex)}")
print(f"     Views:       {int(py_views_exploded):,}")
print(f"     Engagements: {int(py_eng_exploded):,}")

# ─────────────────────────────────────────────────────────────────
# COMPARISON
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("COMPARISON SUMMARY (January 2026)")
print("=" * 60)
print(f"{'Source':<35} {'Views':>12} {'Engagements':>14}")
print("-" * 62)
print(f"{'PHP show_all.php':<35} {int(php_total_views):>12,} {int(php_total_engagements):>14,}")
print(f"{'Python (no explode)':<35} {int(py_views_no_explode):>12,} {int(py_eng_no_explode):>14,}")
print(f"{'Python (with program-explode)':<35} {int(py_views_exploded):>12,} {int(py_eng_exploded):>14,}")
print("-" * 62)
print(f"{'Diff (no-explode vs PHP)':<35} {int(py_views_no_explode - php_total_views):>+12,} {int(py_eng_no_explode - php_total_engagements):>+14,}")
print(f"{'Diff (exploded vs PHP)':<35} {int(py_views_exploded - php_total_views):>+12,} {int(py_eng_exploded - php_total_engagements):>+14,}")

conn.close()
print("\nDone.")
