import psycopg2
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')
cur = conn.cursor()

print("=" * 70)
print("CHECKING DATA INTEGRITY FOR JANUARY 2026")
print("=" * 70)
print()

# Check what's actually in the database
print("1. TOTAL RECORDS:")
cur.execute("""
    SELECT COUNT(*) 
    FROM media_kpis mk
    JOIN media_output mo ON mk.media_id = mo.media_id
    WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
""")
print(f"   Main media rows: {cur.fetchone()[0]}")
print()

# Check platforms data availability
print("2. DATA BY PLATFORM:")
cur.execute("""
    SELECT 
      COUNT(CASE WHEN website_views > 0 THEN 1 END) as website,
      COUNT(CASE WHEN facebook_views > 0 THEN 1 END) as facebook,
      COUNT(CASE WHEN facebook_likes > 0 THEN 1 END) as fb_likes,
      COUNT(CASE WHEN facebook_comments > 0 THEN 1 END) as fb_comments,
      COUNT(CASE WHEN youtube_views > 0 THEN 1 END) as youtube,
      COUNT(CASE WHEN youtube_likes > 0 THEN 1 END) as yt_likes,
      COUNT(CASE WHEN youtube_comments > 0 THEN 1 END) as yt_comments,
      COUNT(CASE WHEN tiktok_views > 0 THEN 1 END) as tiktok,
      COUNT(CASE WHEN instagram_plays > 0 THEN 1 END) as instagram,
      COUNT(CASE WHEN twitter_impressions > 0 THEN 1 END) as twitter
    FROM media_kpis mk
    JOIN media_output mo ON mk.media_id = mo.media_id
    WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
""")
result = cur.fetchone()
print(f"   Website (views>0):        {result[0]} rows")
print(f"   Facebook (views>0):       {result[1]} rows")
print(f"   Facebook Likes (>0):      {result[2]} rows")
print(f"   Facebook Comments (>0):   {result[3]} rows")
print(f"   YouTube (views>0):        {result[4]} rows")
print(f"   YouTube Likes (>0):       {result[5]} rows")
print(f"   YouTube Comments (>0):    {result[6]} rows")
print(f"   TikTok (views>0):         {result[7]} rows")
print(f"   Instagram (plays>0):      {result[8]} rows")
print(f"   Twitter (impressions>0):  {result[9]} rows")
print()

# Check sum totals
print("3. TOTAL METRICS FROM DB:")
cur.execute("""
    SELECT 
      SUM(COALESCE(website_views, 0)) as web_views,
      SUM(COALESCE(website_event_count, 0)) as web_eng,
      SUM(COALESCE(facebook_views, 0)) as fb_views,
      SUM(COALESCE(facebook_likes, 0)) as fb_likes,
      SUM(COALESCE(facebook_comments, 0)) as fb_comments,
      SUM(COALESCE(youtube_views, 0)) as yt_views,
      SUM(COALESCE(youtube_likes, 0)) as yt_likes,
      SUM(COALESCE(youtube_comments, 0)) as yt_comments,
      SUM(COALESCE(tiktok_views, 0)) as tt_views,
      SUM(COALESCE(instagram_plays, 0)) as ig_plays,
      SUM(COALESCE(twitter_impressions, 0)) as tw_imp
    FROM media_kpis mk
    JOIN media_output mo ON mk.media_id = mo.media_id
    WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
""")
result = cur.fetchone()
print(f"   Website Views:        {int(result[0] or 0):,}")
print(f"   Website Engagements:  {int(result[1] or 0):,}")
print(f"   Facebook Views:       {int(result[2] or 0):,}")
print(f"   Facebook Likes:       {int(result[3] or 0):,}")
print(f"   Facebook Comments:    {int(result[4] or 0):,}")
print(f"   YouTube Views:        {int(result[5] or 0):,}")
print(f"   YouTube Likes:        {int(result[6] or 0):,}")
print(f"   YouTube Comments:     {int(result[7] or 0):,}")
print(f"   TikTok Views:         {int(result[8] or 0):,}")
print(f"   Instagram Plays:      {int(result[9] or 0):,}")
print(f"   Twitter Impressions:  {int(result[10] or 0):,}")
print()

# Show your exported totals
print("4. YOUR EXPORTED TOTALS:")
print(f"   Website Views:        9,150")
print(f"   Website Engagements:  24,550")
print(f"   Likes + Comments:     (unknown from your mention)")
print()

# Calculate engagement using app.py logic
print("5. CALCULATED ENGAGEMENTS (using app.py logic):")
cur.execute("""
    SELECT 
      mo.media_id,
      mo.title,
      mk.website_event_count,
      mk.facebook_views,
      mk.facebook_comments + mk.facebook_views + mk.facebook_shares + 
      mk.facebook_likes + mk.facebook_love + mk.facebook_haha + 
      mk.facebook_wow + mk.facebook_sad + mk.facebook_angry + 
      mk.facebook_link_clicks as fb_eng,
      mk.youtube_views,
      mk.youtube_likes + mk.youtube_views + mk.youtube_comments + 
      mk.youtube_shares + mk.youtube_card_clicks as yt_eng
    FROM media_kpis mk
    JOIN media_output mo ON mk.media_id = mo.media_id
    WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
    LIMIT 5
""")
print("   First 5 rows:")
for idx, row in enumerate(cur.fetchall(), 1):
    print(f"   Row {idx}: {row[1][:30]}")
    print(f"     Website Events: {row[2]}, FB Views: {row[3]}, FB Eng: {row[4]}, YT Views: {row[9]}, YT Eng: {row[10]}")

conn.close()
