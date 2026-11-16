"""
Check what the actual displayed totals should be for January 2026
based on ONLY the main media_output rows (not parts)
"""
import psycopg2
import pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

# Get ONLY main media_output rows - matching what should be in export
sql = '''
SELECT 
    mo.media_id,
    mk.website_views,
    mk.website_event_count,
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
    mk.youtube_views,
    mk.youtube_likes,
    mk.youtube_comments,
    mk.youtube_shares,
    mk.youtube_card_clicks,
    mk.source_youtube_views,
    mk.source_youtube_likes,
    mk.source_youtube_comments,
    mk.instagram_plays,
    mk.instagram_engagements,
    mk.twitter_impressions,
    mk.twitter_total_engagement,
    mk.tiktok_views,
    mk.tiktok_engagements
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
ORDER BY mo.media_id
'''

df = pd.read_sql_query(sql, conn)

def n(v):
    try:
        val = float(v)
        return 0.0 if val != val else val
    except (TypeError, ValueError):
        return 0.0

print("MAIN MEDIA OUTPUT ROWS ONLY (without parts):")
print("=" * 70)
print(f"Number of rows: {len(df)}")
print()

# Website only
website_views = sum(df['website_views'].apply(n))
website_eng = sum(df['website_event_count'].apply(n))

print(f"Website Views (sum of column): {int(website_views):,}")
print(f"Website Engagements (sum of column): {int(website_eng):,}")
print()

# Now check: does adding YouTube source views to website views get us closer?
youtube_source = sum(df['source_youtube_views'].apply(n))
print(f"Website Views + YouTube Source Views: {int(website_views + youtube_source):,}")
print(f"  (If this = 9150, then views include source YouTube)")
print()

# Check total across all platforms
total_views = 0
total_engagements = 0

total_views += website_views
total_engagements += website_eng

# YouTube source
yt_source = sum(df['source_youtube_views'].apply(n))
yt_source_eng = sum(df['source_youtube_likes'].apply(n)) + sum(df['source_youtube_comments'].apply(n))
total_views += yt_source
total_engagements += yt_source_eng

# YouTube
yt_views = sum(df['youtube_views'].apply(n))
for idx, row in df.iterrows():
    if n(row['youtube_views']) > 0:
        yt_eng = n(row['youtube_likes']) + n(row['youtube_comments']) + n(row['youtube_shares']) + n(row['youtube_card_clicks'])
        total_engagements += yt_eng
total_views += yt_views

# Facebook
fb = sum(df['facebook_views'].apply(n))
for idx, row in df.iterrows():
    if n(row['facebook_views']) > 0:
        fb_eng = (n(row['facebook_comments']) + n(row['facebook_shares']) + n(row['facebook_likes']) +
                  n(row['facebook_love']) + n(row['facebook_haha']) + n(row['facebook_wow']) +
                  n(row['facebook_sad']) + n(row['facebook_angry']) + n(row['facebook_link_clicks']))
        total_engagements += fb_eng
total_views += fb

# Instagram
ig = sum(df['instagram_plays'].apply(n))
ig_eng = sum(df['instagram_engagements'].apply(n))
total_views += ig
total_engagements += ig_eng

# Twitter
tw = sum(df['twitter_impressions'].apply(n))
tw_eng = sum(df['twitter_total_engagement'].apply(n))
total_views += tw
total_engagements += tw_eng

# TikTok
tt = sum(df['tiktok_views'].apply(n))
tt_eng = sum(df['tiktok_engagements'].apply(n))
total_views += tt
total_engagements += tt_eng

print("-" * 70)
print(f"TOTAL ALL PLATFORMS: {int(total_views):,} views | {int(total_engagements):,} engagements")
print()
print("User's manual sum: 9,150 views | 24,550 engagements")
print()
if int(website_views) == 9150:
    print("✅ Match! User is summing ONLY Website Views column")
else:
    print(f"❌ Mismatch. Website Views = {int(website_views)}, not 9,150")

conn.close()
