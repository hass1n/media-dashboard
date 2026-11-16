"""
Calculate the correct totals by summing all platforms for each row,
matching what the PHP dashboard SHOULD display
"""
import psycopg2

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')
cur = conn.cursor()

# Get ALL media_output rows (no parts) for January 2026
sql = '''
SELECT 
    mo.media_id,
    mo.title,
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
ORDER BY mo.media_date DESC, mo.media_id DESC
'''

cur.execute(sql)
rows = cur.fetchall()

def n(v):
    try:
        return float(v) if v else 0
    except:
        return 0

total_views_all_platforms = 0
total_engagements_all_platforms = 0

website_views_sum = 0
website_eng_sum = 0

print("Calculating totals for all 34 main rows:")
print()

for row in rows:
    # Views
    website_views = n(row[2])
    facebook_views = n(row[4])
    youtube_views = n(row[14])
    source_youtube_views = n(row[19])
    instagram_views = n(row[23])
    twitter_views = n(row[25])
    tiktok_views = n(row[27])
    
    row_total_views = (website_views + facebook_views + youtube_views + 
                       source_youtube_views + instagram_views + twitter_views + tiktok_views)
    
    # Engagements
    website_eng = n(row[3])
    instagram_eng = n(row[24])
    twitter_eng = n(row[26])
    tiktok_eng = n(row[28])
    
    # Facebook engagements (only if views > 0)
    facebook_eng = 0
    if facebook_views > 0:
        facebook_eng = (n(row[5]) + n(row[6]) + n(row[7]) + n(row[8]) + 
                       n(row[9]) + n(row[10]) + n(row[11]) + n(row[12]) + n(row[13]))
    
    # YouTube engagements (only if views > 0)
    youtube_eng = 0
    if youtube_views > 0:
        youtube_eng = n(row[15]) + n(row[16]) + n(row[17]) + n(row[18])
    
    # Source YouTube engagements
    source_youtube_eng = n(row[20]) + n(row[21])
    
    row_total_eng = (website_eng + facebook_eng + youtube_eng + 
                     source_youtube_eng + instagram_eng + twitter_eng + tiktok_eng)
    
    total_views_all_platforms += row_total_views
    total_engagements_all_platforms += row_total_eng
    
    website_views_sum += website_views
    website_eng_sum += website_eng

print(f"Number of main rows: 34")
print()
print(f"Website Views only (column sum): {int(website_views_sum):,}")
print(f"Website Engagements only (column sum): {int(website_eng_sum):,}")
print()
print(f"Total Views (ALL platforms): {int(total_views_all_platforms):,}")
print(f"Total Engagements (ALL platforms): {int(total_engagements_all_platforms):,}")
print()
print("Your manual count: 9,150 views | 24,550 engagements")
print()
if int(website_views_sum) == 9150:
    print("MATCH! Your 9,150 = Website Views column sum")
else:
    print(f"Your 9,150 vs Database Website Views: {int(website_views_sum)}")
    
if int(website_eng_sum) == 24550:
    print("MATCH! Your 24,550 = Website Engagements column sum")
else:
    print(f"Your 24,550 vs Database Website Engagements: {int(website_eng_sum)}")

conn.close()
