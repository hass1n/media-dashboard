import psycopg2
import pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

# Get ALL metrics for January 2026 - matching what show_all.php totals
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

total_views = 0
total_engagements = 0

print("BREAKDOWN BY PLATFORM (Main media_output rows only):")
print("-" * 70)

websites = sum(df['website_views'].apply(n))
website_eng = sum(df['website_event_count'].apply(n))
print(f"Website Views: {int(websites):>10,} | Website Engagements: {int(website_eng):>10,}")
total_views += websites
total_engagements += website_eng

yt_source = sum(df['source_youtube_views'].apply(n))
yt_source_eng = sum(df['source_youtube_likes'].apply(n)) + sum(df['source_youtube_comments'].apply(n))
print(f"YouTube (Source) Views: {int(yt_source):>10,} | Engagements: {int(yt_source_eng):>10,}")
total_views += yt_source
total_engagements += yt_source_eng

for idx, row in df.iterrows():
    if n(row['youtube_views']) > 0:
        yt_eng = n(row['youtube_likes']) + n(row['youtube_comments']) + n(row['youtube_shares']) + n(row['youtube_card_clicks'])
        total_engagements += yt_eng
yt_views = sum(df['youtube_views'].apply(n))
print(f"YouTube Views: {int(yt_views):>10,} | Engagements: (conditional)")
total_views += yt_views

fb = sum(df['facebook_views'].apply(n))
for idx, row in df.iterrows():
    if n(row['facebook_views']) > 0:
        fb_eng = (n(row['facebook_comments']) + n(row['facebook_shares']) + n(row['facebook_likes']) +
                  n(row['facebook_love']) + n(row['facebook_haha']) + n(row['facebook_wow']) +
                  n(row['facebook_sad']) + n(row['facebook_angry']) + n(row['facebook_link_clicks']))
        total_engagements += fb_eng
print(f"Facebook Views: {int(fb):>10,} | Engagements: (conditional)")
total_views += fb

ig = sum(df['instagram_plays'].apply(n))
ig_eng = sum(df['instagram_engagements'].apply(n))
print(f"Instagram Views: {int(ig):>10,} | Engagements: {int(ig_eng):>10,}")
total_views += ig
total_engagements += ig_eng

tw = sum(df['twitter_impressions'].apply(n))
tw_eng = sum(df['twitter_total_engagement'].apply(n))
print(f"Twitter Views: {int(tw):>10,} | Engagements: {int(tw_eng):>10,}")
total_views += tw
total_engagements += tw_eng

tt = sum(df['tiktok_views'].apply(n))
tt_eng = sum(df['tiktok_engagements'].apply(n))
print(f"TikTok Views: {int(tt):>10,} | Engagements: {int(tt_eng):>10,}")
total_views += tt
total_engagements += tt_eng

print("-" * 70)
print(f"TOTAL Views: {int(total_views):,} | TOTAL Engagements: {int(total_engagements):,}")

conn.close()
