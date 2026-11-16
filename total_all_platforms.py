"""
Calculate TOTAL Views and Engagements across ALL PLATFORMS
for January 2026 (main rows only, not parts)
"""
import psycopg2
import pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

sql = '''
SELECT 
    mo.media_id,
    mk.website_views,
    mk.website_event_count AS website_engagements,
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

print("=" * 80)
print("JANUARY 2026 - ALL PLATFORMS (Main Media Only)")
print("=" * 80)
print()

# Calculate views by platform
website_views = sum(df['website_views'].apply(n))
youtube_views = sum(df['youtube_views'].apply(n))
youtube_source_views = sum(df['source_youtube_views'].apply(n))
facebook_views = sum(df['facebook_views'].apply(n))
instagram_views = sum(df['instagram_plays'].apply(n))
twitter_views = sum(df['twitter_impressions'].apply(n))
tiktok_views = sum(df['tiktok_views'].apply(n))

total_views = website_views + youtube_views + youtube_source_views + facebook_views + instagram_views + twitter_views + tiktok_views

print("VIEWS BY PLATFORM:")
print("-" * 80)
print(f"  Website Views:                {int(website_views):>10,}")
print(f"  YouTube Views:                {int(youtube_views):>10,}")
print(f"  YouTube (Source) Views:       {int(youtube_source_views):>10,}")
print(f"  Facebook Views:               {int(facebook_views):>10,}")
print(f"  Instagram Views:              {int(instagram_views):>10,}")
print(f"  Twitter Impressions:          {int(twitter_views):>10,}")
print(f"  TikTok Views:                 {int(tiktok_views):>10,}")
print("-" * 80)
print(f"  TOTAL VIEWS:                  {int(total_views):>10,}")
print()

# Calculate engagements by platform
website_engagements = sum(df['website_engagements'].apply(n))

youtube_engagements = 0
for idx, row in df.iterrows():
    if n(row['youtube_views']) > 0:
        yt_eng = n(row['youtube_likes']) + n(row['youtube_comments']) + n(row['youtube_shares']) + n(row['youtube_card_clicks'])
        youtube_engagements += yt_eng

youtube_source_engagements = sum(df['source_youtube_likes'].apply(n)) + sum(df['source_youtube_comments'].apply(n))

facebook_engagements = 0
for idx, row in df.iterrows():
    if n(row['facebook_views']) > 0:
        fb_eng = (n(row['facebook_comments']) + n(row['facebook_shares']) + n(row['facebook_likes']) +
                  n(row['facebook_love']) + n(row['facebook_haha']) + n(row['facebook_wow']) +
                  n(row['facebook_sad']) + n(row['facebook_angry']) + n(row['facebook_link_clicks']))
        facebook_engagements += fb_eng

instagram_engagements = sum(df['instagram_engagements'].apply(n))
twitter_engagements = sum(df['twitter_total_engagement'].apply(n))
tiktok_engagements = sum(df['tiktok_engagements'].apply(n))

total_engagements = (website_engagements + youtube_engagements + youtube_source_engagements + 
                     facebook_engagements + instagram_engagements + twitter_engagements + tiktok_engagements)

print("ENGAGEMENTS BY PLATFORM:")
print("-" * 80)
print(f"  Website Engagements:          {int(website_engagements):>10,}")
print(f"  YouTube Engagements:          {int(youtube_engagements):>10,}")
print(f"  YouTube (Source) Engagements: {int(youtube_source_engagements):>10,}")
print(f"  Facebook Engagements:         {int(facebook_engagements):>10,}")
print(f"  Instagram Engagements:        {int(instagram_engagements):>10,}")
print(f"  Twitter Engagements:          {int(twitter_engagements):>10,}")
print(f"  TikTok Engagements:           {int(tiktok_engagements):>10,}")
print("-" * 80)
print(f"  TOTAL ENGAGEMENTS:            {int(total_engagements):>10,}")
print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total Views (All Platforms):       {int(total_views):,}")
print(f"Total Engagements (All Platforms): {int(total_engagements):,}")
print()
print("Your manual count: 9,150 views | 24,550 engagements")
print()
if int(website_views) == 9150:
    print("Note: Your 9,150 = Website Views ONLY")
if int(website_engagements) == 24550:
    print("Note: Your 24,550 = Website Engagements ONLY")

conn.close()
