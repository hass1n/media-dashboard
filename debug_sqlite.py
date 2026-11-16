import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = 'local_media.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print('='*60)
print('CHECKING local_media.db FOR JANUARY 2026')
print('='*60)

# Check tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables found:', tables)

# Try to compute sums similar to Postgres checks
query = '''
SELECT COUNT(*) as total_rows,
       SUM(COALESCE(mk.website_views,0)) as web_views,
       SUM(COALESCE(mk.website_event_count,0)) as web_eng,
       SUM(COALESCE(mk.facebook_views,0)) as fb_views,
       SUM(COALESCE(mk.facebook_likes,0)) as fb_likes,
       SUM(COALESCE(mk.facebook_comments,0)) as fb_comments,
       SUM(COALESCE(mk.youtube_views,0)) as yt_views,
       SUM(COALESCE(mk.youtube_likes,0)) as yt_likes,
       SUM(COALESCE(mk.youtube_comments,0)) as yt_comments,
       SUM(COALESCE(mk.tiktok_views,0)) as tt_views,
       SUM(COALESCE(mk.instagram_plays,0)) as ig_plays,
       SUM(COALESCE(mk.twitter_impressions,0)) as tw_imp
FROM media_kpis mk
JOIN media_output mo ON mk.media_id = mo.media_id
WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
'''

try:
    cur.execute(query)
    row = cur.fetchone()
    if row:
        print(f"Total rows: {row[0]}")
        print(f"Website Views: {row[1]}")
        print(f"Website Engagements: {row[2]}")
        print(f"Facebook Views: {row[3]}")
        print(f"Facebook Likes: {row[4]}")
        print(f"Facebook Comments: {row[5]}")
        print(f"YouTube Views: {row[6]}")
        print(f"YouTube Likes: {row[7]}")
        print(f"YouTube Comments: {row[8]}")
        print(f"TikTok Views: {row[9]}")
        print(f"Instagram Plays: {row[10]}")
        print(f"Twitter Impressions: {row[11]}")
    else:
        print('No rows returned')
except Exception as e:
    print('Query failed:', e)

conn.close()
