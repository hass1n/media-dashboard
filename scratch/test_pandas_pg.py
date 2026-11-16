import psycopg2
import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

def get_db_connection():
    return psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

def get_unified_media_df(start_date, end_date):
    conn = get_db_connection()
    query = """
    SELECT 
        mo.media_id::text AS media_id,
        mo.media_date AS date,
        mo.media_source,
        (SELECT string_agg(author_name, ',') FROM media_authors WHERE media_id = mo.media_id) AS author,
        (SELECT string_agg(media_type, ',') FROM media_types WHERE media_id = mo.media_id) AS output,
        (SELECT string_agg(media_program, ',') FROM media_programs WHERE media_id = mo.media_id) AS programs,
        (SELECT string_agg(media_category, ',') FROM media_categories WHERE media_id = mo.media_id) AS categories,
        (SELECT COUNT(copy_id) FROM media_copies WHERE media_id = mo.media_id) AS copies,
        mk.facebook_views,
        (COALESCE(mk.facebook_comments, 0) + COALESCE(mk.facebook_shares, 0) + COALESCE(mk.facebook_likes, 0) + COALESCE(mk.facebook_love, 0) + COALESCE(mk.facebook_haha, 0) + COALESCE(mk.facebook_wow, 0) + COALESCE(mk.facebook_sad, 0) + COALESCE(mk.facebook_angry, 0) + COALESCE(mk.facebook_link_clicks, 0)) AS facebook_total_engagments,
        (COALESCE(mk.facebook_comments, 0) + COALESCE(mk.facebook_shares, 0) + COALESCE(mk.facebook_likes, 0) + COALESCE(mk.facebook_love, 0) + COALESCE(mk.facebook_haha, 0) + COALESCE(mk.facebook_wow, 0) + COALESCE(mk.facebook_link_clicks, 0)) AS facebook_positive_engagment,
        COALESCE(mk.facebook_comments, 0) + COALESCE(mk.facebook_shares, 0) + COALESCE(mk.facebook_likes, 0) + COALESCE(mk.facebook_love, 0) + COALESCE(mk.facebook_haha, 0) + COALESCE(mk.facebook_wow, 0) + COALESCE(mk.facebook_link_clicks, 0) AS facebook_post_engagment,
        mk.youtube_views,
        mk.source_youtube_views,
        mk.youtube_likes,
        mk.youtube_comments,
        mk.youtube_shares,
        mk.youtube_card_clicks,
        (COALESCE(mk.youtube_likes, 0) + COALESCE(mk.youtube_comments, 0) + COALESCE(mk.youtube_shares, 0) + COALESCE(mk.youtube_card_clicks, 0)) AS youtube_engagments,
        mk.website_views,
        mk.website_total_users AS web_total_users,
        mk.website_event_count AS website_engagments,
        mk.website_duration AS website_average_duration,
        mk.twitter_impressions,
        mk.twitter_total_engagement,
        mk.twitter_likes,
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
        mo.media_source,
        (SELECT string_agg(author_name, ',') FROM media_authors WHERE media_id = mo.media_id) AS author,
        (SELECT string_agg(media_type, ',') FROM media_types WHERE media_id = mo.media_id) AS output,
        (SELECT string_agg(part_program_name, ',') FROM parts_programs WHERE part_id = mp.part_id) AS programs,
        (SELECT string_agg(media_category, ',') FROM media_categories WHERE media_id = mo.media_id) AS categories,
        0 AS copies,
        pk.part_facebook_views AS facebook_views,
        (COALESCE(pk.part_facebook_comments, 0) + COALESCE(pk.part_facebook_shares, 0) + COALESCE(pk.part_facebook_likes, 0) + COALESCE(pk.part_facebook_love, 0) + COALESCE(pk.part_facebook_haha, 0) + COALESCE(pk.part_facebook_wow, 0) + COALESCE(pk.part_facebook_sad, 0) + COALESCE(pk.part_facebook_angry, 0) + COALESCE(pk.part_facebook_link_clicks, 0)) AS facebook_total_engagments,
        (COALESCE(pk.part_facebook_comments, 0) + COALESCE(pk.part_facebook_shares, 0) + COALESCE(pk.part_facebook_likes, 0) + COALESCE(pk.part_facebook_love, 0) + COALESCE(pk.part_facebook_haha, 0) + COALESCE(pk.part_facebook_wow, 0) + COALESCE(pk.part_facebook_link_clicks, 0)) AS facebook_positive_engagment,
        COALESCE(pk.part_facebook_comments, 0) + COALESCE(pk.part_facebook_shares, 0) + COALESCE(pk.part_facebook_likes, 0) + COALESCE(pk.part_facebook_love, 0) + COALESCE(pk.part_facebook_haha, 0) + COALESCE(pk.part_facebook_wow, 0) + COALESCE(pk.part_facebook_link_clicks, 0) AS facebook_post_engagment,
        pk.part_youtube_views AS youtube_views,
        0 AS source_youtube_views,
        pk.part_youtube_likes AS youtube_likes,
        pk.part_youtube_comments AS youtube_comments,
        pk.part_youtube_shares AS youtube_shares,
        pk.part_youtube_card_clicks AS youtube_card_clicks,
        (COALESCE(pk.part_youtube_likes, 0) + COALESCE(pk.part_youtube_comments, 0) + COALESCE(pk.part_youtube_shares, 0) + COALESCE(pk.part_youtube_card_clicks, 0)) AS youtube_engagments,
        pk.part_website_views AS website_views,
        pk.part_website_total_users AS web_total_users,
        pk.part_website_event_count AS website_engagments,
        pk.part_website_duration AS website_average_duration,
        pk.part_twitter_impressions AS twitter_impressions,
        pk.part_twitter_total_engagement,
        pk.part_twitter_likes AS twitter_likes,
        pk.part_tiktok_views AS tiktok_views,
        pk.part_tiktok_engagements AS tiktok_engagments,
        pk.part_instagram_plays AS insta_views,
        pk.part_instagram_engagements AS instagram_engagment
    FROM media_parts mp
    JOIN media_output mo ON mp.media_id = mo.media_id
    LEFT JOIN parts_kpis pk ON mp.part_id = pk.part_id
    WHERE mo.media_date BETWEEN %s AND %s
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date, start_date, end_date))
    conn.close()
    return df

if __name__ == '__main__':
    df = get_unified_media_df('2020-01-01', '2026-12-31')
    print("Records loaded:", len(df))
    print(df[['media_id', 'date', 'programs', 'copies', 'facebook_positive_engagment', 'youtube_engagments']].head())
