import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('local_media.db')
cur = conn.cursor()

query = '''
SELECT COUNT(*) as rows,
       SUM(COALESCE(website_views,0)) as web_views,
       SUM(COALESCE(website_engagments,0)) as web_eng,
       SUM(COALESCE(facebook_views,0)) as fb_views,
       SUM(COALESCE(facebook_total_engagments,0)) as fb_eng,
       SUM(COALESCE(insta_views,0)) as ig_views,
       SUM(COALESCE(instagram_engagment,0)) as ig_eng,
       SUM(COALESCE(youtube_views,0)) as yt_views,
       SUM(COALESCE(youtube_engagments,0)) as yt_eng,
       SUM(COALESCE(tiktok_views,0)) as tt_views,
       SUM(COALESCE(tiktok_engagments,0)) as tt_eng
FROM unified_media
WHERE date BETWEEN '2026-01-01' AND '2026-01-31'
'''
cur.execute(query)
row = cur.fetchone()
print('UNIFIED MEDIA JAN 2026:')
print(f'  Rows: {row[0]}')
print(f'  Website Views: {row[1]}')
print(f'  Website Engagements: {row[2]}')
print(f'  Facebook Views: {row[3]}')
print(f'  Facebook Engagements: {row[4]}')
print(f'  Instagram Views: {row[5]}')
print(f'  Instagram Engagements: {row[6]}')
print(f'  YouTube Views: {row[7]}')
print(f'  YouTube Engagements: {row[8]}')
print(f'  TikTok Views: {row[9]}')
print(f'  TikTok Engagements: {row[10]}')
conn.close()
