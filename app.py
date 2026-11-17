from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import json
from PIL import Image, ImageDraw
from urllib.parse import unquote

# List of keywords that represent media output rather than specific programs
# Used to filter out media names from the Programs list and charts
MEDIA_KEYWORDS = [
    'VDL', 'ALJADEED', 'OTV', 'LBCI', 'MTV', 'NBN', 'FUTURE TV', 'AL MANAR', 'LIMSLB', 
    'BEIRUT24', 'NBNLB', 'LBCI.COM', 'ALARABY', 'ANNAHAR', 'JANOUBIA', 'SAWTALCHAEB', 
    'SBI', 'SPOTSHOT', 'LEBANON24', 'ALMODON', 'MANAR', 'AL GHAD', 'ALJOUMHOURIA', 
    'ALIWAA', 'LEBANONDEBATE', 'ELMARADA', 'ANADOL', 'VDTL', 'AL ESTIKLAL', 'SPUTNIK', 
    'HADATHONLINE', 'YEMENTODAY', 'CIPE', 'NIDAA AL WATAN', 'FRANCE 24', 'ANNAHAR TV', 
    'ARABI 21', 'TRT ARABI', 'DARAJ.COM', 'LIBAN LIBRE', 'INDEPENDENT ARABIA', 'ALARABIA', 
    'RLL', 'RADIO LIBAN LIBRE', 'AL HORA', 'ADDDIYAR', 'TAYYAR.ORG', 'AL JAZEERA',
    'AL ARAB', 'LEBANON 24', 'AL MAJALLA', 'EL EKTISAD', 'ALGHAD', 'ALJOUMHOURIA',
    'LEBECONOMY', 'ALSHARK AL AWSAT', 'NOW LEBANON', 'AL HIWAR NEWS', 'MEDIA NEWS FACTORY',
    'AL JADEED', 'AL BINAA', 'ASAS MEDIA', 'ASSAS MEDIA', 'NIDAA AL WATAN', 'AKHBARALYAWM',
    'ENTREVUE', 'ASHARQBUSINESS', 'ANBAAONLINE', 'NEW GHANA', 'ALAMSAR', 'ALSAFANEWS',
    'JOURNAL DES LIBERTES', 'AL YAWM TV', 'ATLAS NETWORK', 'BUSINESS ECHOES', 'EXECUTIVE',
    'GRANDLB', 'ALBORSA NEWS', 'ALKALIMA ONLINE', 'AKHBAR ALYAWM', 'XINHUANET', 'NRK',
    'LEBANESEFORCES', 'AL-AIN', 'KHALEEJ TIMES', 'ENOOMA', 'LBC', 'ALTAHARRI', 'SPOT SHOT',
    'EL ESTIKLAL', 'ARAB MAJALLA', 'CH23', 'SAWT KOL LOBNAN', 'SAWT BEIRUT INTERNATIONAL',
    'XINHUA NET', 'SHARQ AWSAT', 'AKHBAR AL AN', 'NEW LEBANON', 'ALMARKAZIA', 'SHAFAQANA',
    'ALAFKAR', 'AL SHAREK', 'INDEPENDENT ARABIA', 'LEBANON ECONOMY FILES', 'LIRARATE',
    'AL DIYAR', 'ALANBAA', 'MAJALLA', 'ADDIYAR', 'AL DIYAR'
]

import psycopg2
import sqlalchemy
from sqlalchemy import create_engine
import warnings

def _load_env_file(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')):
    """Load KEY=VALUE lines from .env into os.environ (existing env vars win)."""
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

_load_env_file()

# Database Credentials (set in .env, see .env.example)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "media_db_4")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "")

# Create SQLAlchemy engine (URL.create escapes special characters in the password)
engine = create_engine(sqlalchemy.engine.URL.create(
    "postgresql", username=DB_USER, password=DB_PASS,
    host=DB_HOST, port=int(DB_PORT), database=DB_NAME,
))

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

app = Flask(__name__)
PHOTO_DIR = os.path.join(os.path.dirname(__file__), 'photos')
CIRCLE_PHOTO_DIR = os.path.join(PHOTO_DIR, 'circle')

@app.route('/author_image/<path:filename>')
def author_image(filename):
    if filename.startswith('circle/'):
        return send_from_directory(CIRCLE_PHOTO_DIR, filename[len('circle/'):])
    return send_from_directory(PHOTO_DIR, filename)


def normalize_author_name(name):
    return ''.join(ch for ch in str(name).lower() if ch.isalnum())


def filter_comma_separated_exact(df, field_name, value):
    target = str(value).strip().casefold()
    matches = df[field_name].fillna('').astype(str).str.split(',').map(
        lambda parts: any(part.strip().casefold() == target for part in parts)
    )
    return df[matches].copy()


def get_author_photo_filename(author_name):
    target = normalize_author_name(author_name)
    if not target:
        return None

    try:
        for filename in os.listdir(PHOTO_DIR):
            base, ext = os.path.splitext(filename)
            if ext.lower() not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                continue
            if normalize_author_name(base) == target:
                return filename
    except FileNotFoundError:
        return None

    return None


def ensure_circle_photo_dir():
    os.makedirs(CIRCLE_PHOTO_DIR, exist_ok=True)


def get_author_photo_circle_filename(author_name):
    source_filename = get_author_photo_filename(author_name)
    if not source_filename:
        return None

    ensure_circle_photo_dir()
    base, _ = os.path.splitext(source_filename)
    circle_filename = f"{base}_circle.png"
    circle_path = os.path.join(CIRCLE_PHOTO_DIR, circle_filename)
    if os.path.exists(circle_path):
        return f"circle/{circle_filename}"

    source_path = os.path.join(PHOTO_DIR, source_filename)
    try:
        with Image.open(source_path).convert('RGBA') as img:
            size = min(img.size)
            img = img.resize((size, size), Image.LANCZOS)
            mask = Image.new('L', img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
            img.putalpha(mask)

            # Add a white circular border/background for better chart visibility.
            circle_bg = Image.new('RGBA', img.size, (255, 255, 255, 0))
            bg_draw = ImageDraw.Draw(circle_bg)
            bg_draw.ellipse((0, 0, img.size[0], img.size[1]), fill=(255, 255, 255, 255))
            circle_bg.paste(img, (0, 0), img)
            circle_bg.save(circle_path, format='PNG')
    except Exception:
        return None

    return f"circle/{circle_filename}"


def get_image_as_data_uri(photo_filename):
    """Return a base64 data URI for the given photo filename (relative to PHOTO_DIR)."""
    import base64
    if photo_filename.startswith('circle/'):
        img_path = os.path.join(CIRCLE_PHOTO_DIR, photo_filename[len('circle/'):])
    else:
        img_path = os.path.join(PHOTO_DIR, photo_filename)
    try:
        with open(img_path, 'rb') as f:
            data = f.read()
        ext = os.path.splitext(img_path)[1].lower().lstrip('.')
        mime = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'webp': 'webp', 'gif': 'gif'}.get(ext, 'png')
        b64 = base64.b64encode(data).decode('utf-8')
        return f"data:image/{mime};base64,{b64}"
    except Exception:
        return None


def add_author_images_to_bar_chart(fig, auth_counts, image_size_fraction=0.5):
    if auth_counts.empty:
        return

    images = []
    max_value = auth_counts['interviews'].max() if not auth_counts.empty else 1

    # Use a fixed y-axis range based on max_value so the chart height is predictable.
    # Images are sized as a fixed fraction of the y-axis range — this means all photos
    # appear the same visual size regardless of individual bar heights.
    # This fixes the "damaged image" issue when one author dominates (e.g. 814 vs 82).
    y_top    = max_value * 1.8    # total y-axis ceiling
    img_size = y_top * image_size_fraction
    gap      = y_top * 0.08       # fixed gap to leave room for the number text

    for _, row in auth_counts.iterrows():
        author_name = row['author']
        photo_filename = get_author_photo_circle_filename(author_name)
        if not photo_filename:
            continue

        # Use a base64 data URI so Plotly.js can display the image without
        # making a separate HTTP request (relative URLs are unreliable in
        # embedded Plotly HTML on Windows / behind proxies).
        image_source = get_image_as_data_uri(photo_filename)
        if not image_source:
            continue

        images.append({
            'source': image_source,
            'x': author_name,
            'xref': 'x',
            'y': float(row['interviews']) + gap,
            'yref': 'y',
            'xanchor': 'center',
            'yanchor': 'bottom',
            'sizex': 0.8,
            'sizey': img_size,
            'sizing': 'contain',
            'layer': 'above'
        })

    if images:
        fig.update_layout(
            images=images,
            height=600,
            margin={'t': 120, 'b': 60},
            yaxis={'range': [0, y_top]}
        )
        fig.update_traces(
            textposition='outside',
            textfont={'size': 10},
            marker_line_width=0
        )



def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    return conn

@app.template_filter('intcomma')
def intcomma_filter(value):
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value


def resolve_filter_dates(request_obj):
    """Return the active date range from form values first, then query params."""
    start_date = request_obj.form.get('start_date') or request_obj.args.get('start_date') or '2020-02-01'
    end_date = request_obj.form.get('end_date') or request_obj.args.get('end_date') or '2026-06-01'
    return start_date, end_date


# ==================== KPI AGGREGATION FUNCTIONS ====================

def get_media_platform_metrics(conn, media_id):
    """
    Get platform-specific views and engagements for a media_id from media_kpis.
    Returns a dict with total views and engagement by platform.
    """
    query = """
    SELECT 
        -- Facebook
        COALESCE(facebook_views, 0) as facebook_views,
        (COALESCE(facebook_comments, 0) + COALESCE(facebook_views, 0) + COALESCE(facebook_shares, 0) + COALESCE(facebook_likes, 0) + 
         COALESCE(facebook_love, 0) + COALESCE(facebook_haha, 0) + COALESCE(facebook_wow, 0) + 
         COALESCE(facebook_sad, 0) + COALESCE(facebook_angry, 0) + COALESCE(facebook_link_clicks, 0)) as facebook_engagement,
        -- YouTube (Summing all 'views' columns for YouTube)
        (COALESCE(youtube_views, 0) + COALESCE(source_youtube_views, 0)) as youtube_views,
        (COALESCE(youtube_likes, 0) + COALESCE(youtube_views, 0) + COALESCE(source_youtube_views, 0) + COALESCE(youtube_comments, 0) + COALESCE(youtube_shares, 0) + 
         COALESCE(youtube_card_clicks, 0) + COALESCE(source_youtube_likes, 0) + COALESCE(source_youtube_comments, 0) +
         COALESCE(youtube_watch_time, 0)) as youtube_engagement,
        -- Twitter
        (COALESCE(twitter_views, 0)) as twitter_views,
        (COALESCE(twitter_impressions, 0) + COALESCE(twitter_views, 0) + COALESCE(twitter_likes, 0) + COALESCE(twitter_retweets, 0) + 
         COALESCE(twitter_replies, 0) + COALESCE(twitter_total_engagement, 0)) as twitter_engagement,
        -- TikTok
        COALESCE(tiktok_views, 0) as tiktok_views,
        (COALESCE(tiktok_engagements, 0) + COALESCE(tiktok_views, 0)) as tiktok_engagement,
        -- Instagram (No 'views' column, so views = 0 per user rule)
        0 as instagram_views,
        (COALESCE(instagram_plays, 0) + COALESCE(instagram_engagements, 0)) as instagram_engagement,
        -- Website
        COALESCE(website_views, 0) as website_views,
        COALESCE(website_event_count, 0) as website_engagement,
        COALESCE(source_youtube_views, 0) as source_youtube_views
    FROM media_kpis 
    WHERE media_id = %s
    """
    df = pd.read_sql_query(query, conn, params=(media_id,))
    if df.empty:
        return {
            'youtube_views': 0, 'youtube_engagement': 0,
            'facebook_views': 0, 'facebook_engagement': 0,
            'twitter_views': 0, 'twitter_engagement': 0,
            'tiktok_views': 0, 'tiktok_engagement': 0,
            'instagram_views': 0, 'instagram_engagement': 0,
            'website_views': 0, 'website_engagement': 0,
            'source_youtube_views': 0,
            'total_views': 0, 'total_engagement': 0
        }
    
    row = df.iloc[0]
    metrics = {
        'youtube_views': int(row['youtube_views']),
        'youtube_engagement': int(row['youtube_engagement']),
        'facebook_views': int(row['facebook_views']),
        'facebook_engagement': int(row['facebook_engagement']),
        'twitter_views': int(row['twitter_views']),
        'twitter_engagement': int(row['twitter_engagement']),
        'tiktok_views': int(row['tiktok_views']),
        'tiktok_engagement': int(row['tiktok_engagement']),
        'instagram_views': int(row['instagram_views']),
        'instagram_engagement': int(row['instagram_engagement']),
        'website_views': int(row['website_views']),
        'website_engagement': int(row['website_engagement']),
        'source_youtube_views': int(row['source_youtube_views']),
    }
    metrics['total_views'] = sum(metrics[k] for k in metrics if 'views' in k and k != 'source_youtube_views')
    metrics['total_engagement'] = sum(metrics[k] for k in metrics if 'engagement' in k)
    return metrics

def get_part_platform_metrics(conn, part_id):
    """
    Get platform-specific views and engagements for a part_id from parts_kpis.
    Returns a dict with total views and engagement by platform.
    """
    query = """
    SELECT 
        -- Facebook
        COALESCE(part_facebook_views, 0) as facebook_views,
        (COALESCE(part_facebook_comments, 0) + COALESCE(part_facebook_views, 0) + COALESCE(part_facebook_shares, 0) + COALESCE(part_facebook_likes, 0) + 
         COALESCE(part_facebook_love, 0) + COALESCE(part_facebook_haha, 0) + COALESCE(part_facebook_wow, 0) + 
         COALESCE(part_facebook_sad, 0) + COALESCE(part_facebook_angry, 0) + COALESCE(part_facebook_link_clicks, 0)) as facebook_engagement,
        -- YouTube
        COALESCE(part_youtube_views, 0) as youtube_views,
        (COALESCE(part_youtube_likes, 0) + COALESCE(part_youtube_views, 0) + COALESCE(part_youtube_comments, 0) + COALESCE(part_youtube_shares, 0) + 
         COALESCE(part_youtube_card_clicks, 0) + COALESCE(part_youtube_watch_time, 0)) as youtube_engagement,
        -- Twitter
        COALESCE(part_twitter_views, 0) as twitter_views,
        (COALESCE(part_twitter_impressions, 0) + COALESCE(part_twitter_views, 0) + COALESCE(part_twitter_likes, 0) + COALESCE(part_twitter_retweets, 0) + 
         COALESCE(part_twitter_replies, 0) + COALESCE(part_twitter_total_engagement, 0)) as twitter_engagement,
        -- TikTok
        COALESCE(part_tiktok_views, 0) as tiktok_views,
        (COALESCE(part_tiktok_engagements, 0) + COALESCE(part_tiktok_views, 0)) as tiktok_engagement,
        -- Instagram
        0 as instagram_views,
        (COALESCE(part_instagram_plays, 0) + COALESCE(part_instagram_engagements, 0)) as instagram_engagement,
        -- Website
        COALESCE(part_website_views, 0) as website_views,
        COALESCE(part_website_event_count, 0) as website_engagement
    FROM parts_kpis 
    WHERE part_id = %s
    """
    df = pd.read_sql_query(query, conn, params=(part_id,))
    if df.empty:
        return {
            'youtube_views': 0, 'youtube_engagement': 0,
            'facebook_views': 0, 'facebook_engagement': 0,
            'twitter_views': 0, 'twitter_engagement': 0,
            'tiktok_views': 0, 'tiktok_engagement': 0,
            'instagram_views': 0, 'instagram_engagement': 0,
            'website_views': 0, 'website_engagement': 0,
            'total_views': 0, 'total_engagement': 0
        }
    
    row = df.iloc[0]
    metrics = {
        'youtube_views': int(row['youtube_views']),
        'youtube_engagement': int(row['youtube_engagement']),
        'facebook_views': int(row['facebook_views']),
        'facebook_engagement': int(row['facebook_engagement']),
        'twitter_views': int(row['twitter_views']),
        'twitter_engagement': int(row['twitter_engagement']),
        'tiktok_views': int(row['tiktok_views']),
        'tiktok_engagement': int(row['tiktok_engagement']),
        'instagram_views': int(row['instagram_views']),
        'instagram_engagement': int(row['instagram_engagement']),
        'website_views': int(row['website_views']),
        'website_engagement': int(row['website_engagement']),
    }
    metrics['total_views'] = sum(metrics[k] for k in metrics if 'views' in k)
    metrics['total_engagement'] = sum(metrics[k] for k in metrics if 'engagement' in k)
    return metrics

def get_aggregated_media_kpis(conn, media_id):
    """
    Get aggregated KPIs for a media including all its parts.
    Sums views and engagements across the media and all its parts.
    """
    # Get media-level metrics
    media_metrics = get_media_platform_metrics(conn, media_id)
    
    # Get all parts for this media and their metrics
    query = "SELECT part_id FROM media_parts WHERE media_id = %s"
    parts_df = pd.read_sql_query(query, conn, params=(media_id,))
    
    aggregated = media_metrics.copy()
    
    for _, part_row in parts_df.iterrows():
        part_id = part_row['part_id']
        part_metrics = get_part_platform_metrics(conn, part_id)
        
        # Sum metrics across platforms
        aggregated['youtube_views'] += part_metrics['youtube_views']
        aggregated['youtube_engagement'] += part_metrics['youtube_engagement']
        aggregated['facebook_views'] += part_metrics['facebook_views']
        aggregated['facebook_engagement'] += part_metrics['facebook_engagement']
        aggregated['twitter_views'] += part_metrics['twitter_views']
        aggregated['twitter_engagement'] += part_metrics['twitter_engagement']
        aggregated['tiktok_views'] += part_metrics['tiktok_views']
        aggregated['tiktok_engagement'] += part_metrics['tiktok_engagement']
        aggregated['instagram_views'] += part_metrics['instagram_views']
        aggregated['instagram_engagement'] += part_metrics['instagram_engagement']
        aggregated['website_views'] += part_metrics['website_views']
        aggregated['website_engagement'] += part_metrics['website_engagement']
    
    # Recalculate totals
    aggregated['total_views'] = (aggregated['youtube_views'] + aggregated['facebook_views'] + 
                                  aggregated['twitter_views'] + aggregated['tiktok_views'] + 
                                  aggregated['instagram_views'] + aggregated['website_views'])
    aggregated['total_engagement'] = (aggregated['youtube_engagement'] + aggregated['facebook_engagement'] + 
                                       aggregated['twitter_engagement'] + aggregated['tiktok_engagement'] + 
                                       aggregated['instagram_engagement'] + aggregated['website_engagement'])
    
    return aggregated

# ==================== END KPI AGGREGATION FUNCTIONS ====================

def get_unified_media_df(start_date, end_date):
    conn = get_db_connection()
    # Query that aggregates parts' KPIs into their parent media
    query = """
    SELECT 
        mo.media_id::text AS media_id,
        mo.title,
        mo.title_english,
        mo.media_date AS date,
        mo.media_source,
        mo.media_source_link AS source_link,
        mo.media_whatsapp AS whatsapp_sent,
        mo.media_youtube_link AS youtube_link,
        mo.youtube_date,
        mo.media_lebanonmatters_status AS status,
        mo.media_facebook_link AS facebook_link,
        mo.media_instagram_link AS instagram_link,
        mo.media_twitter_link AS twitter_link,
        mo.media_tiktok_link AS tiktok_link,
        (SELECT string_agg(author_name, ',') FROM media_authors WHERE media_id = mo.media_id) AS author,
        (SELECT string_agg(media_type, ',') FROM media_types WHERE media_id = mo.media_id) AS output,
        (SELECT string_agg(media_program, ',') FROM media_programs WHERE media_id = mo.media_id) AS programs,
        (SELECT string_agg(media_category, ',') FROM media_categories WHERE media_id = mo.media_id) AS categories,
        '' AS tags,
        (SELECT COUNT(copy_id) FROM media_copies WHERE media_id = mo.media_id) AS copies,
        -- Media KPIs combined with summed parts KPIs
        -- Facebook
        COALESCE(mk.facebook_views, 0) + COALESCE(SUM(pk.part_facebook_views), 0) AS facebook_views,
        -- ###############
        (COALESCE(mk.facebook_likes, 0) + COALESCE(mk.facebook_love, 0) + COALESCE(mk.facebook_haha, 0) + COALESCE(mk.facebook_wow, 0)) + 
        COALESCE(SUM(COALESCE(pk.part_facebook_likes, 0) + COALESCE(pk.part_facebook_love, 0) + COALESCE(pk.part_facebook_haha, 0) + COALESCE(pk.part_facebook_wow, 0)), 0) AS facebook_positive_engagment,
        -- ###############
        (COALESCE(mk.facebook_comments, 0) + COALESCE(mk.facebook_views, 0) + COALESCE(mk.facebook_shares, 0) + COALESCE(mk.facebook_likes, 0) + COALESCE(mk.facebook_love, 0) + COALESCE(mk.facebook_haha, 0) + COALESCE(mk.facebook_wow, 0) + COALESCE(mk.facebook_sad, 0) + COALESCE(mk.facebook_angry, 0) + COALESCE(mk.facebook_link_clicks, 0)) + 
        COALESCE(SUM(COALESCE(pk.part_facebook_comments, 0) + COALESCE(pk.part_facebook_views, 0) + COALESCE(pk.part_facebook_shares, 0) + COALESCE(pk.part_facebook_likes, 0) + COALESCE(pk.part_facebook_love, 0) + COALESCE(pk.part_facebook_haha, 0) + COALESCE(pk.part_facebook_wow, 0) + COALESCE(pk.part_facebook_sad, 0) + COALESCE(pk.part_facebook_angry, 0) + COALESCE(pk.part_facebook_link_clicks, 0)), 0) AS facebook_total_engagments,
        -- YouTube
        (COALESCE(mk.youtube_views, 0) + COALESCE(mk.source_youtube_views, 0)) + COALESCE(SUM(pk.part_youtube_views), 0) AS youtube_views,
        (COALESCE(mk.youtube_likes, 0) + COALESCE(mk.source_youtube_likes, 0)) + COALESCE(SUM(pk.part_youtube_likes), 0) AS youtube_likes,
        (COALESCE(mk.youtube_likes, 0) + COALESCE(mk.youtube_views, 0) + COALESCE(mk.source_youtube_views, 0) + COALESCE(mk.youtube_comments, 0) + COALESCE(mk.youtube_shares, 0) + COALESCE(mk.youtube_card_clicks, 0) + COALESCE(mk.source_youtube_likes, 0) + COALESCE(mk.source_youtube_comments, 0) + COALESCE(mk.youtube_watch_time, 0)) + 
        COALESCE(SUM(COALESCE(pk.part_youtube_likes, 0) + COALESCE(pk.part_youtube_views, 0) + COALESCE(pk.part_youtube_comments, 0) + COALESCE(pk.part_youtube_shares, 0) + COALESCE(pk.part_youtube_card_clicks, 0) + COALESCE(pk.part_youtube_watch_time, 0)), 0) AS youtube_engagments,
        COALESCE(mk.source_youtube_views, 0) AS source_youtube_views,
        COALESCE(mk.source_youtube_likes, 0) AS source_likes_youtube,
        COALESCE(mk.source_youtube_comments, 0) AS source_youtube_comments,
        -- Twitter
        COALESCE(mk.twitter_views, 0) + COALESCE(SUM(pk.part_twitter_views), 0) AS twitter_views,
        COALESCE(mk.twitter_likes, 0) + COALESCE(SUM(pk.part_twitter_likes), 0) AS twitter_likes,
        (COALESCE(mk.twitter_impressions, 0) + COALESCE(mk.twitter_total_engagement, 0)) + 
        COALESCE(SUM(COALESCE(pk.part_twitter_impressions, 0) + COALESCE(pk.part_twitter_total_engagement, 0)), 0) AS twitter_total_engagment,
        COALESCE(mk.twitter_impressions, 0) + COALESCE(SUM(pk.part_twitter_impressions), 0) AS twitter_impressions,
        -- Website
        COALESCE(SUM(mk.website_views), 0) + COALESCE(SUM(pk.part_website_views), 0) AS website_views,
        COALESCE(mk.website_event_count, 0) + COALESCE(SUM(pk.part_website_event_count), 0) AS website_engagments,
        COALESCE(mk.website_total_users, 0) + COALESCE(SUM(pk.part_website_total_users), 0) AS web_total_users,
        to_char(mk.website_duration, 'HH24:MI:SS') AS website_average_duration,
        -- YouTube watch time (media + parts)
        COALESCE(mk.youtube_watch_time, 0) + COALESCE(SUM(pk.part_youtube_watch_time), 0) AS youtube_watch_time,
        -- TikTok
        COALESCE(mk.tiktok_views, 0) + COALESCE(SUM(pk.part_tiktok_views), 0) AS tiktok_views,
        COALESCE(mk.tiktok_engagements, 0) + COALESCE(mk.tiktok_views, 0) + COALESCE(SUM(COALESCE(pk.part_tiktok_engagements, 0) + COALESCE(pk.part_tiktok_views, 0)), 0) AS tiktok_engagments,
        -- Instagram
        COALESCE(mk.instagram_plays, 0) + COALESCE(SUM(pk.part_instagram_plays), 0) AS insta_views,
        (COALESCE(mk.instagram_plays, 0) + COALESCE(mk.instagram_engagements, 0)) + COALESCE(SUM(COALESCE(pk.part_instagram_plays, 0) + COALESCE(pk.part_instagram_engagements, 0)), 0) AS instagram_engagment
    FROM media_output mo
    LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
    LEFT JOIN media_parts mp ON mo.media_id = mp.media_id
    LEFT JOIN parts_kpis pk ON mp.part_id = pk.part_id
    WHERE mo.media_date BETWEEN %s AND %s
    GROUP BY mo.media_id, mo.title, mo.title_english, mo.media_date, mo.media_source, 
             mo.media_source_link, mo.media_whatsapp, mo.media_youtube_link, 
             mo.youtube_date, mo.media_lebanonmatters_status, 
             mo.media_facebook_link, mo.media_instagram_link, mo.media_twitter_link, 
             mo.media_tiktok_link, mk.facebook_views, mk.facebook_comments, mk.facebook_shares, 
             mk.facebook_likes, mk.facebook_love, mk.facebook_haha, mk.facebook_wow, mk.facebook_sad, 
             mk.facebook_angry, mk.facebook_link_clicks, mk.youtube_views, mk.source_youtube_views, 
             mk.source_youtube_likes, mk.source_youtube_comments, mk.youtube_likes, mk.youtube_comments, 
             mk.youtube_shares, mk.youtube_card_clicks, mk.youtube_watch_time, mk.website_views, 
             mk.website_total_users, mk.website_event_count, mk.website_duration, mk.twitter_impressions, 
             mk.twitter_total_engagement, mk.twitter_likes, mk.tiktok_views, mk.tiktok_engagements, 
             mk.instagram_plays, mk.instagram_engagements, mk.twitter_views, mk.twitter_retweets, 
             mk.twitter_replies, mk.website_engagement_rate
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()
    return df

def normalize_csv_first_value(value):
    """Return the first non-empty value from a comma-separated field."""
    if pd.isna(value):
        return ''

    items = [str(v).strip() for v in str(value).split(',')]
    cleaned = [item for item in items if item and item.lower() not in {'nan', 'none', 'unknown'}]
    return cleaned[0] if cleaned else ''


def prepare_presence_base(df):
    """Return one canonical row per media_id for all presence charts.

    Every chart uses the same filtered media-id set, with missing values normalized to
    a fallback label instead of being silently dropped. This keeps totals aligned across
    authors, programs, media outputs, and output types.
    """
    base = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    if base.empty:
        return base

    base = base.drop_duplicates(subset=['media_id']).copy()

    for col in ['author', 'programs', 'media_source', 'output']:
        if col not in base.columns:
            continue

        base[col] = base[col].apply(normalize_csv_first_value)

        if col == 'author':
            base = base[base[col].astype(str).str.strip() != ''].copy()
        elif col == 'programs':
            base[col] = base[col].fillna('').astype(str).str.strip().str.upper()
            base[col] = base[col].replace({'': 'OTHER/UNKNOWN'})
            base = base[~base[col].isin(MEDIA_KEYWORDS)].copy()
        elif col == 'media_source':
            base[col] = base[col].fillna('').astype(str).str.strip().str.upper()
            base[col] = base[col].replace({'': 'OTHER/UNKNOWN'})
        elif col == 'output':
            base[col] = base[col].fillna('').astype(str).str.strip()
            base[col] = base[col].replace({'': 'Other/Unknown', 'NAN': 'Other/Unknown', 'NONE': 'Other/Unknown', 'UNKNOWN': 'Other/Unknown'})

    return base


def build_presence_counts(df, field_name, label_name):
    """Count presence totals by splitting comma-separated values into distinct entries."""
    base = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    if base.empty:
        return pd.DataFrame(columns=[label_name, 'interviews'])

    if field_name not in base.columns:
        return pd.DataFrame(columns=[label_name, 'interviews'])

    base = base.copy()
    base['weight'] = 1

    def split_field_values(values):
        split_values = []
        for value in values:
            if pd.isna(value) or str(value).strip() == '':
                split_values.append(['OTHER/UNKNOWN' if field_name in {'programs', 'media_source'} else 'Other/Unknown'])
                continue

            items = [str(v).strip() for v in str(value).split(',')]
            cleaned = [item for item in items if item and item.lower() not in {'nan', 'none', 'unknown'}]
            if not cleaned:
                cleaned = ['OTHER/UNKNOWN' if field_name in {'programs', 'media_source'} else 'Other/Unknown']
            split_values.append(cleaned)
        return split_values

    exploded = base.assign(__values__=split_field_values(base[field_name])).explode('__values__')
    exploded[field_name] = exploded['__values__']
    exploded = exploded.drop(columns=['__values__'])
    exploded = exploded.drop_duplicates(subset=['media_id', field_name]).copy()

    if field_name == 'author':
        exploded[field_name] = exploded[field_name].fillna('').astype(str).str.strip()
        exploded[field_name] = exploded[field_name].replace({'': 'Other/Unknown'})
        exploded = exploded[~exploded[field_name].isin(['', 'nan', 'none', 'unknown'])].copy()
    elif field_name == 'programs':
        exploded[field_name] = exploded[field_name].fillna('OTHER/UNKNOWN').astype(str).str.strip().str.upper()
        exploded = exploded[~exploded[field_name].isin(MEDIA_KEYWORDS)].copy()
    elif field_name == 'media_source':
        exploded[field_name] = exploded[field_name].fillna('OTHER/UNKNOWN').astype(str).str.strip().str.upper()
    elif field_name == 'output':
        exploded[field_name] = exploded[field_name].fillna('Other/Unknown').astype(str).str.strip()
        exploded[field_name] = exploded[field_name].replace({'NAN': 'Other/Unknown', 'NONE': 'Other/Unknown', 'UNKNOWN': 'Other/Unknown'})

    counts = exploded.groupby(field_name, dropna=False)['weight'].sum().reset_index()
    counts.columns = [label_name, 'interviews']
    return counts.sort_values(by='interviews', ascending=False).reset_index(drop=True)


def get_presence_counts(df, field_name, label_name):
    """Return presence totals, counting an interview once per listed value."""
    if field_name in {'programs', 'author'}:
        return build_presence_counts(df, field_name, label_name)

    base = prepare_presence_base(df)
    if base.empty or field_name not in base.columns:
        return pd.DataFrame(columns=[label_name, 'interviews'])

    counts = base.groupby(field_name, dropna=False).size().reset_index(name='interviews')
    counts.columns = [label_name, 'interviews']
    return counts.sort_values(by='interviews', ascending=False).reset_index(drop=True)


def standardize_media_name(media_name):
    """Standardize media output names to handle variations and group them together"""
    if pd.isna(media_name) or media_name == '':
        return ''
    
    import re
    media = str(media_name).strip().lower()
    # Normalize spaces
    media = re.sub(r'\s+', ' ', media)
    
    # Priority grouping logic (specific matches first)
    if 'independent' in media and 'arabia' in media or 'independant' in media or media in ['independent', 'independentarabia']:
        return 'INDEPENDENT ARABIA'
    elif 'sky news' in media or 'skynews' in media:
        return 'SKY NEWS ARABIA'
    elif 'france 24' in media or 'france24' in media:
        return 'FRANCE 24'
    elif 'arabi 21' in media or 'arabi21' in media:
        return 'ARABI 21'
    elif 'al araby' in media or 'alaraby' in media or 'araby.co.uk' in media:
        return 'AL ARABY'
    elif 'arabiya' in media or 'arabia' in media or 'alarbiya' in media:
        return 'AL ARABIYA'
    elif 'jadeed' in media:
        return 'AL JADEED'
    elif 'jazeera' in media or 'jazira' in media:
        return 'AL JAZEERA'
    elif 'mtv' in media:
        return 'MTV'
    elif 'lbci' in media or 'lbc' in media:
        return 'LBCI'
    elif 'annahar' in media or 'al nahar' in media or 'alnahar' in media or 'النهار' in media:
        return 'ANNAHAR'
    elif 'estiklal' in media or 'esteklel' in media or 'istiklal' in media or 'isteklel' in media or 'استقلال' in media or 'إستقلال' in media:
        return 'AL ESTIKLAL'
    elif 'nidaa' in media and 'watan' in media or 'nidaalwatan' in media:
        return 'NIDAA AL WATAN'
    elif 'lebanon 24' in media or 'lebanon24' in media:
        return 'LEBANON 24'
    elif 'sbi' in media or 'sawt beirut' in media:
        return 'SAWT BEIRUT'
    elif 'vdl' in media or 'vdtl' in media:
        return 'VDL'
    elif 'otv' in media:
        return 'OTV'
    elif 'nbn' in media:
        return 'NBN'
    elif 'future' in media and 'tv' in media:
        return 'FUTURE TV'
    elif 'al manar' in media or 'almanar' in media or 'manar' in media:
        return 'AL MANAR'
    elif 'asharq' in media or 'al shark' in media or 'alshark' in media or 'sharq' in media or 'elshark' in media:
        return 'ASHARQ'
    elif 'joumhouria' in media or 'joumhouriya' in media:
        return 'AL JOUMHOURIA'
    elif 'janoubia' in media:
        return 'JANOUBIA'
    elif 'anadol' in media:
        return 'ANADOLU'
    elif 'xinhua' in media:
        return 'XINHUA'
    elif 'tele liban' in media or 'teleliban' in media:
        return 'TELE LIBAN'
    elif 'al liwaa' in media or 'aliwaa' in media or 'alliwaa' in media or 'liwaa' in media:
        return 'AL LIWAA'
    elif 'al majalla' in media or 'al majala' in media or 'majalla' in media:
        return 'AL MAJALLA'
    elif 'al monitor' in media or 'al-monitor' in media:
        return 'AL MONITOR'
    elif 'lebanese forces' in media or 'lebaneseforces' in media or 'lebanease' in media:
        return 'LEBANESE FORCES'
    elif 'lebeconomy' in media or 'leb economy' in media or 'lebanoneconomy' in media:
        return 'LEB ECONOMY'
    elif 'lirarate' in media:
        return 'LIRARATE'
    elif 'spot shot' in media or 'spotshot' in media or 'sopt shot' in media:
        return 'SPOT SHOT'
    elif 'radio liban libre' in media or 'rll' in media:
        return 'RADIO LIBAN LIBRE'
    elif 'radio liban' in media or 'radioliban' in media:
        return 'RADIO LIBAN'
    elif 'al yawm' in media or 'alyawm' in media or 'alyaum' in media or 'yawm' in media:
        return 'AL YAWM'
    elif 'al hurra' in media or 'alhorra' in media or 'al hourra' in media or 'alhurra' in media or 'hurriya' in media:
        return 'AL HURRA'
    elif 'ahram' in media:
        return 'AHRAM ONLINE'
    elif 'akhbar' in media and 'an' in media or 'akhbaralaan' in media:
        return 'AKHBAR AL AN'
    elif 'akhbar' in media and 'yawm' in media or 'akhbaralyawm' in media:
        return 'AKHBAR AL YAWM'
    elif 'al diyar' in media or 'al diyyar' in media or 'addiyar' in media or 'adiyyar' in media or 'aldiyar' in media:
        return 'AL DIYAR'
    elif 'al arab' in media or 'alarab' in media:
        return 'AL ARAB'
    elif 'anbaa' in media or 'alanbaa' in media or 'alanba' in media:
        return 'AL ANBAA'
    elif 'beirut 24' in media or 'beirut24' in media:
        return 'BEIRUT 24'
    elif 'daraj' in media:
        return 'DARAJ'
    elif 'nashra' in media or 'elnashra' in media:
        return 'EL NASHRA'
    elif 'marada' in media or 'elmarada' in media:
        return 'AL MARADA'
    elif 'hadath' in media:
        return 'AL HADATH'
    elif 'hona' in media and 'loubnan' in media or 'honalobnan' in media or 'هنا لبنان' in media:
        return 'HONA LOUBNAN'
    elif 'ici beyrouth' in media or 'icibeyrouth' in media:
        return 'ICI BEYROUTH'
    elif 'lebanon debate' in media or 'lebanondebate' in media:
        return 'LEBANON DEBATE'
    elif 'lebanon on' in media or 'lebanonon' in media:
        return 'LEBANON ON'
    elif 'raseef' in media or 'rasseef' in media or 'rassif' in media:
        return 'RASEEF22'
    elif 'sputnik' in media:
        return 'SPUTNIK'
    elif 'trt' in media:
        return 'TRT ARABI'
    elif 'yemen' in media and 'today' in media or 'yamanalyawm' in media or 'اليمن اليوم' in media:
        return 'YEMEN TODAY'
    elif 'mamlaka' in media:
        return 'AL MAMLAKA'
    elif 'sawt' in media and 'sha' in media or 'sawtalchaeb' in media:
        return 'SAWT AL SHAAB'
    
    return str(media_name).strip().upper()


def build_performance_chart(df, title, group_by='programs', chart_height=500):
    """Build a fit platform chart with exactly Views and Engagements legends."""
    platform_columns = {
        'Facebook': ('facebook_views', 'facebook_total_engagments'),
        'YouTube': ('youtube_views', 'youtube_engagments'),
        'Instagram': ('insta_views', 'instagram_engagment'),
        'Twitter': ('twitter_views', 'twitter_total_engagment'),
        'TikTok': ('tiktok_views', 'tiktok_engagments'),
        'Website': ('website_views', 'website_engagments')
    }
    chart_rows = []
    for platform, (views_column, engagements_column) in platform_columns.items():
        views_values = df[views_column] if views_column in df.columns else pd.Series(dtype='float64')
        engagements_values = df[engagements_column] if engagements_column in df.columns else pd.Series(dtype='float64')
        views = pd.to_numeric(views_values, errors='coerce').fillna(0).sum()
        engagements = pd.to_numeric(engagements_values, errors='coerce').fillna(0).sum()
        chart_rows.extend([
            {'Platform': platform, 'Metric': 'Views', 'Value': views},
            {'Platform': platform, 'Metric': 'Engagements', 'Value': engagements}
        ])

    chart_data = pd.DataFrame(chart_rows)
    fig = px.bar(
        chart_data, x='Platform', y='Value', color='Metric', barmode='group',
        title=title,
        labels={'Platform': 'Platform', 'Value': 'Total', 'Metric': 'Metric'},
        text_auto='.2s',
        color_discrete_map={'Views': '#087f8c', 'Engagements': '#f4a261'}
    )
    fig.update_layout(
        height=chart_height, xaxis_tickangle=0, bargap=0.28,
        margin=dict(l=35, r=25, t=65, b=55), legend_title_text='',
        plot_bgcolor='#f8fbfc', paper_bgcolor='white',
        title={'font': {'size': 16, 'color': '#244454'}, 'x': 0.03},
        xaxis={'automargin': True, 'title': {'font': {'size': 12}}},
        yaxis={'automargin': True, 'title': {'text': 'Total', 'font': {'size': 12}}},
        legend={'orientation': 'h', 'y': 1.02, 'yanchor': 'bottom', 'x': 1, 'xanchor': 'right'}
    )
    fig.update_traces(textposition='outside', cliponaxis=False)
    return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'responsive': True})


def build_home_dashboard_charts(df, start_date=None, end_date=None, include_engagement_charts=True, include_excluded_outputs=False):
    """Build the standard dashboard card set with optional engagement cards."""
    working_df = df.copy()
    working_df['media_source'] = working_df['media_source'].apply(standardize_media_name)
    working_df['weight'] = 1

    def normalize_output_parts(value):
        if pd.isna(value):
            return []
        return [p.strip().lower() for p in str(value).split(',') if p.strip()]

    if not include_excluded_outputs:
        exclude_list = ['economic update', 'research', 'conference', 'economic updates', 'economic news']
        def should_exclude(val):
            if pd.isna(val):
                return False
            parts = normalize_output_parts(val)
            return any(p in exclude_list for p in parts)
        working_df = working_df[~working_df['output'].apply(should_exclude)]

    if include_excluded_outputs:
        home_dashboard_df = df.copy()
        home_dashboard_df['media_source'] = home_dashboard_df['media_source'].apply(standardize_media_name)
        home_dashboard_df['weight'] = 1
        exclude_list = ['economic update', 'research', 'conference', 'economic updates', 'economic news']
        def should_exclude(val):
            if pd.isna(val):
                return False
            parts = normalize_output_parts(val)
            return any(p in exclude_list for p in parts)
        home_dashboard_df = home_dashboard_df[~home_dashboard_df['output'].apply(should_exclude)]
        home_dashboard_output_df = home_dashboard_df[~home_dashboard_df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
        home_dashboard_output_df['output'] = home_dashboard_output_df['output'].fillna('Other/Unknown')
        home_dashboard_output_df.loc[home_dashboard_output_df['output'].str.strip() == '', 'output'] = 'Other/Unknown'
        home_dashboard_output_df['output'] = home_dashboard_output_df['output'].astype(str).apply(
            lambda x: x.split(',')[0].strip() if x.strip() else 'Other/Unknown'
        )
        home_dashboard_types = set(
            home_dashboard_output_df.drop_duplicates(subset=['media_id'])['output']
            .astype(str).str.strip().str.lower()
        )

        def row_has_home_dashboard_type(row):
            return any(part in home_dashboard_types for part in normalize_output_parts(row['output']))

        working_df = working_df[~working_df.apply(row_has_home_dashboard_type, axis=1)]

    prog_counts = get_presence_counts(working_df, 'programs', 'program')
    if not prog_counts.empty:
        other_mask = prog_counts['program'] == 'OTHER'
        if other_mask.any():
            other_index = prog_counts[other_mask].index[0]
            prog_counts = prog_counts.loc[:other_index].reset_index(drop=True)

    total_prog_sum = int(prog_counts['interviews'].sum()) if not prog_counts.empty else 0
    fig_prog = px.bar(
        prog_counts,
        x='program',
        y='interviews',
        color='interviews',
        custom_data=['program'],
                 title=(f"Number of other outputs per program (Total: {total_prog_sum})" if include_excluded_outputs
                     else f"Numbers of interviews per programs (Total: {total_prog_sum})"),
            labels={'program': 'Program Name', 'interviews': str(total_prog_sum)},
        text_auto=True,
        color_continuous_scale='Blues'
    )
    fig_prog.update_layout(showlegend=False, xaxis_tickangle=-45, bargap=0.6,
                           margin=dict(l=20, r=20, t=40, b=40),
                           title={'font': {'size': 14}},
                           xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}},
                           yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}})
    fig_prog.update_traces(width=0.6, textfont={'size': 10}, textposition='outside', cliponaxis=False)

    outlets_df = working_df[~working_df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    outlets_df['media_source'] = outlets_df['media_source'].fillna('Other/Unknown')
    outlets_df.loc[outlets_df['media_source'].str.strip() == '', 'media_source'] = 'Other/Unknown'
    outlets_df = outlets_df.drop_duplicates(subset=['media_id'])

    if not outlets_df.empty:
        outlets_df.loc[:, 'media_source'] = outlets_df['media_source'].str.strip().str.upper()
        all_outlet_counts = outlets_df.groupby('media_source')['weight'].sum().reset_index()
        all_outlet_counts.columns = ['outlet', 'interviews']
        all_outlet_counts = all_outlet_counts.sort_values(by='interviews', ascending=False)
        top_outlet_counts = all_outlet_counts.head(15)
    else:
        all_outlet_counts = pd.DataFrame(columns=['outlet', 'interviews'])
        top_outlet_counts = pd.DataFrame(columns=['outlet', 'interviews'])

    total_outlet_sum = int(all_outlet_counts['interviews'].sum()) if not all_outlet_counts.empty else 0
    preview_outlet_sum = total_outlet_sum
    fig_outlets_preview = px.bar(top_outlet_counts, x='outlet', y='interviews', color='interviews',
                                 title=f"Numbers of interviews per media output (Total: {preview_outlet_sum})",
                                 labels={'outlet': 'Media Output', 'interviews': 'Interviews'},
                                 text_auto=True,
                                 color_continuous_scale='Blues')
    fig_outlets_preview.update_layout(showlegend=False, xaxis_tickangle=-45, bargap=0.45,
                                      margin=dict(l=18, r=18, t=40, b=52),
                                      title={'font': {'size': 14}, 'x': 0.5},
                                      xaxis={'tickfont': {'size': 10}, 'title': {'text': 'Media Output', 'font': {'size': 11}}, 'automargin': True},
                                      yaxis={'tickfont': {'size': 10}, 'title': {'text': 'Interviews', 'font': {'size': 11}}, 'automargin': True})
    fig_outlets_preview.update_traces(width=0.55, textposition='outside', textfont={'size': 10}, cliponaxis=False)

    chart_width = max(1200, len(all_outlet_counts) * 40)
    fig_outlets_all = px.bar(all_outlet_counts, x='outlet', y='interviews', color='interviews',
                             title=f"Numbers of interviews per media output (Total: {total_outlet_sum})",
                             labels={'outlet': 'Media Output', 'interviews': 'Interviews'},
                             text_auto=True,
                             color_continuous_scale='Blues',
                             width=chart_width)
    fig_outlets_all.update_layout(showlegend=False, xaxis_tickangle=-45, bargap=0.45,
                                  margin=dict(l=18, r=18, t=40, b=52),
                                  title={'font': {'size': 14}, 'x': 0.5},
                                  xaxis={'automargin': True, 'title': {'text': 'Media Output', 'font': {'size': 11}}},
                                  yaxis={'title': {'text': 'Interviews', 'font': {'size': 11}}})
    fig_outlets_all.update_traces(width=0.55, textposition='outside', textfont={'size': 10}, cliponaxis=False)

    out_df = working_df[~working_df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    out_df['output'] = out_df['output'].fillna('Other/Unknown')
    out_df.loc[out_df['output'].str.strip() == '', 'output'] = 'Other/Unknown'
    out_df['output'] = out_df['output'].astype(str).apply(lambda x: x.split(',')[0].strip() if x.strip() else 'Other/Unknown')
    out_exploded = out_df.drop_duplicates(subset=['media_id'])
    out_counts = out_exploded['output'].value_counts().reset_index()
    out_counts.columns = ['category', 'count']
    total_out_sum = int(out_counts['count'].sum()) if not out_counts.empty else 0
    fig_out = px.bar(out_counts, x='category', y='count', color='count',
                     title=(f"Number of other outputs per output type (Total: {total_out_sum})" if include_excluded_outputs
                            else f"Number of interviews per media type (Total: {total_out_sum})"),
                     labels={'category': 'Output Category', 'count': str(total_out_sum)},
                     text_auto=True,
                     color_continuous_scale='Blues')
    fig_out.update_layout(showlegend=False, legend_title="Output Types", bargap=0.6,
                          margin=dict(l=20, r=20, t=40, b=40),
                          title={'font': {'size': 14}},
                          legend=dict(font=dict(size=10)),
                          xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}},
                          yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}})
    fig_out.update_yaxes(title_text=str(total_out_sum))
    fig_out.update_traces(width=0.6, textposition='outside', cliponaxis=False)

    auth_counts = get_presence_counts(working_df, 'author', 'author')
    if auth_counts.empty:
        auth_counts = pd.DataFrame(columns=['author', 'interviews'])
    total_auth_sum = str(int(auth_counts['interviews'].sum())) if not auth_counts.empty else "0"
    fig_auth = px.bar(auth_counts, x='author', y='interviews', color='interviews',
                      title=("Number of other outputs per author" if include_excluded_outputs
                             else "Number of interviews per authors"),
                      labels={'author': 'Author', 'interviews': f"Total Count: {total_auth_sum}"},
                      text_auto=True,
                      color_continuous_scale='Greens')
    fig_auth.update_layout(showlegend=False, xaxis_tickangle=-45, coloraxis_showscale=False,
                           paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', autosize=True,
                           height=700, margin=dict(l=0, r=0, t=0, b=0),
                           title={'font': {'size': 14, 'color': '#2c3e50'}, 'x': 0.05, 'y': 0.95},
                           xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}, 'gridcolor': 'rgba(0,0,0,0)', 'automargin': True},
                           yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}, 'gridcolor': '#f0f0f0', 'automargin': True})
    fig_auth.update_traces(textposition='outside', textfont={'size': 10}, marker_line_width=0)
    add_author_images_to_bar_chart(fig_auth, auth_counts)
    fig_auth.update_layout(margin=dict(l=20, r=20, t=40, b=40))

    charts = {
        'programs': pio.to_html(fig_prog, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'outlets_preview': pio.to_html(fig_outlets_preview, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'outlets_all': pio.to_html(fig_outlets_all, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'outputs': pio.to_html(fig_out, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'authors': pio.to_html(fig_auth, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'outlet_show_more': len(all_outlet_counts) > len(top_outlet_counts)
    }
    charts['performance'] = build_performance_chart(
        working_df,
        f"Social Media and Website Views and Engagements ({start_date} to {end_date})"
    )

    platform_totals = {}
    total_views = 0
    total_engagements = 0
    if include_engagement_charts:
        df_exploded = working_df.copy()
        df_exploded['programs'] = df_exploded['programs'].astype(str).str.split(',')
        df_exploded = df_exploded.explode('programs')
        df_exploded['programs'] = df_exploded['programs'].str.strip().str.upper()
        df_exploded = df_exploded[df_exploded['programs'] != '']
        df_exploded = df_exploded[~df_exploded['programs'].isin(MEDIA_KEYWORDS)]
        df_exploded = df_exploded.drop_duplicates(subset=['media_id', 'programs'])

        social_platforms = ['facebook', 'youtube', 'twitter', 'tiktok', 'instagram']
        combined_stats = []
        for platform in social_platforms:
            if platform == 'facebook':
                v = pd.to_numeric(working_df['facebook_views'], errors='coerce').fillna(0).sum()
                e = pd.to_numeric(working_df['facebook_total_engagments'], errors='coerce').fillna(0).sum()
            elif platform == 'youtube':
                v = pd.to_numeric(working_df['youtube_views'], errors='coerce').fillna(0).sum()
                e = pd.to_numeric(working_df['youtube_engagments'], errors='coerce').fillna(0).sum()
            elif platform == 'twitter':
                v = pd.to_numeric(working_df['twitter_views'], errors='coerce').fillna(0).sum()
                e = pd.to_numeric(working_df['twitter_total_engagment'], errors='coerce').fillna(0).sum()
            elif platform == 'tiktok':
                v = pd.to_numeric(working_df['tiktok_views'], errors='coerce').fillna(0).sum()
                e = pd.to_numeric(working_df['tiktok_engagments'], errors='coerce').fillna(0).sum()
            elif platform == 'instagram':
                v = pd.to_numeric(working_df['insta_views'], errors='coerce').fillna(0).sum()
                e = pd.to_numeric(working_df['instagram_engagment'], errors='coerce').fillna(0).sum()
            combined_stats.append({'platform': platform.capitalize(), 'views': v, 'engagements': e})

        social_data = pd.DataFrame(combined_stats)
        social_colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']
        fig_social = px.bar(social_data, x='platform', y='engagements', color='platform',
                            title=f"Total Engagements ({start_date} to {end_date})",
                            labels={'platform': 'Social Platform', 'engagements': 'Total Engagements'},
                            text_auto='.2s',
                            color_discrete_sequence=px.colors.qualitative.Safe)
        fig_social.update_layout(showlegend=False, legend_title="Platforms", bargap=0.6,
                                 margin=dict(l=20, r=20, t=40, b=40),
                                 title={'font': {'size': 14}},
                                 legend=dict(font=dict(size=10)),
                                 xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}},
                                 yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}})
        fig_social.update_traces(width=0.3, textposition='outside', cliponaxis=False)

        fig_views = px.bar(social_data, x='platform', y='views', color='platform',
                           title=f"Total Views ({start_date} to {end_date})",
                           labels={'platform': 'Social Platform', 'views': 'Total Views'},
                           text_auto='.2s',
                           color_discrete_sequence=px.colors.qualitative.Dark24)
        fig_views.update_layout(showlegend=False, legend_title="Platforms", bargap=0.6,
                                margin=dict(l=20, r=20, t=40, b=40),
                                title={'font': {'size': 14}},
                                legend=dict(font=dict(size=10)),
                                xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}},
                                yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}})
        fig_views.update_traces(width=0.3, textposition='outside', cliponaxis=False)

        web_views = pd.to_numeric(working_df['website_views'], errors='coerce').fillna(0).sum()
        web_eng = pd.to_numeric(working_df['website_engagments'], errors='coerce').fillna(0).sum()
        web_users = pd.to_numeric(working_df['web_total_users'], errors='coerce').fillna(0).sum()
        website_perf = pd.DataFrame([
            {'Metric': 'Website Views', 'Value': web_views},
            {'Metric': 'Website Engagements', 'Value': web_eng},
            {'Metric': 'Total Users', 'Value': web_users},
        ])
        fig_website = px.bar(website_perf, x='Metric', y='Value', color='Metric',
                             title=f"Website Performance ({start_date} to {end_date})",
                             labels={'Value': 'Count', 'Metric': 'Metric'},
                             text_auto='.2s',
                             color_discrete_sequence=['#6610f2', '#e83e8c', '#20c997'])
        fig_website.update_layout(showlegend=False, bargap=0.6,
                                  margin=dict(l=20, r=20, t=40, b=40),
                                  title={'font': {'size': 14}},
                                  xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}},
                                  yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}})
        fig_website.update_traces(width=0.2, textposition='outside', cliponaxis=False)

        charts.update({
            'social': pio.to_html(fig_social, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
            'views': pio.to_html(fig_views, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
            'website': pio.to_html(fig_website, full_html=False, include_plotlyjs='cdn', config={'responsive': True})
        })

        platform_totals = {row['platform'].lower(): {'views': row['views'], 'engagements': row['engagements']} for row in combined_stats}
        total_views = sum(row['views'] for row in combined_stats)
        total_engagements = sum(row['engagements'] for row in combined_stats)

    return charts, platform_totals, total_views, total_engagements


@app.route('/', methods=['GET', 'POST'])
def index():
    start_date, end_date = resolve_filter_dates(request)

    df = get_unified_media_df(start_date, end_date)
    if df.empty:
        return render_template('index.html', charts={}, start_date=start_date, end_date=end_date, no_data=True,
                               include_engagement_charts=True)

    charts, platform_totals, total_views, total_engagements = build_home_dashboard_charts(
        df, start_date=start_date, end_date=end_date, include_engagement_charts=True, include_excluded_outputs=False
    )

    return render_template('index.html',
                           charts=charts,
                           start_date=start_date,
                           end_date=end_date,
                           no_data=False,
                           include_engagement_charts=True,
                           platform_totals=platform_totals,
                           total_views=total_views,
                           total_engagements=total_engagements)


@app.route('/other-media', methods=['GET', 'POST'])
def other_media_dashboard():
    start_date, end_date = resolve_filter_dates(request)

    df = get_unified_media_df(start_date, end_date)
    if df.empty:
        return render_template('index.html', charts={}, start_date=start_date, end_date=end_date, no_data=True,
                               include_engagement_charts=True, page_title='Other Outputs', show_channel_chart=False)

    charts, platform_totals, total_views, total_engagements = build_home_dashboard_charts(
        df, start_date=start_date, end_date=end_date, include_engagement_charts=True, include_excluded_outputs=True
    )

    return render_template('index.html',
                           charts=charts,
                           start_date=start_date,
                           end_date=end_date,
                           no_data=False,
                           include_engagement_charts=True,
                           page_title='Other Outputs',
                           show_channel_chart=False,
                           platform_totals=platform_totals,
                           total_views=total_views,
                           total_engagements=total_engagements)
@app.route('/channels', methods=['GET'])
@app.route('/outputs', methods=['GET'])
def outputs_list():
    start_date, end_date = resolve_filter_dates(request)

    df = get_unified_media_df(start_date, end_date)
    if df.empty:
        return render_template('outputs.html', charts={}, outputs=[], no_data=True, start_date=start_date, end_date=end_date)

    df['media_source'] = df['media_source'].apply(standardize_media_name)
    df['weight'] = 1
    outlets_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    outlets_df['media_source'] = outlets_df['media_source'].fillna('Other/Unknown')
    outlets_df.loc[outlets_df['media_source'].str.strip() == '', 'media_source'] = 'Other/Unknown'
    outlets_df = outlets_df.drop_duplicates(subset=['media_id'])

    if not outlets_df.empty:
        outlets_df.loc[:, 'media_source'] = outlets_df['media_source'].str.strip().str.upper()
        all_outlet_counts = outlets_df.groupby('media_source')['weight'].sum().reset_index()
        all_outlet_counts.columns = ['outlet', 'interviews']
        all_outlet_counts = all_outlet_counts.sort_values(by='interviews', ascending=False)
    else:
        all_outlet_counts = pd.DataFrame(columns=['outlet', 'interviews'])

    total_outlet_all_count = int(all_outlet_counts['interviews'].sum()) if not all_outlet_counts.empty else 0
    top_outlet_counts = all_outlet_counts.head(20)
    fig_outlets_all = px.bar(
        top_outlet_counts, x='interviews', y='outlet', color='interviews',
        orientation='h',
        title=f"Top {len(top_outlet_counts)} Media Channels by Interviews (Total: {total_outlet_all_count})",
        labels={'outlet': 'Media Channel', 'interviews': 'Interviews'},
        text_auto=True,
        color_continuous_scale='Greens'
    )
    fig_outlets_all.update_layout(
        showlegend=False,
        height=max(380, len(top_outlet_counts) * 32 + 140),
        yaxis={'categoryorder': 'total ascending', 'automargin': True, 'ticks': ''},
        xaxis={'automargin': True, 'rangemode': 'tozero'},
        margin=dict(l=40, r=30, t=60, b=45),
        bargap=0.35
    )
    fig_outlets_all.update_traces(
        texttemplate='%{x:,.0f}',
        textposition='inside',
        insidetextanchor='end',
        cliponaxis=True
    )

    charts = {
        'outlets_all': pio.to_html(fig_outlets_all, full_html=False, include_plotlyjs='cdn', config={'responsive': True})
    }
    outputs = all_outlet_counts.to_dict(orient='records')
    return render_template('outputs.html', charts=charts, outputs=outputs, no_data=False, start_date=start_date, end_date=end_date)


@app.route('/media-channels')
def media_channels_list():
    conn = get_db_connection()
    result = pd.read_sql_query(
        "SELECT DISTINCT media_source FROM media_output WHERE media_source IS NOT NULL AND BTRIM(media_source) <> ''",
        conn
    )
    conn.close()
    channels = sorted({
        standardize_media_name(name)
        for name in result['media_source'].dropna()
        if str(name).strip()
    } - {'OTHER/UNKNOWN'})
    return jsonify({'channels': channels})


@app.route('/program/<program_name>', methods=['GET'])
def program_detail(program_name):
    """Display detailed analysis for a specific program"""
    # 1. Decode URL parameters & decode program_name (e.g., %20 to space)
    decoded_program_name = unquote(program_name)
    start_date, end_date = resolve_filter_dates(request)
    
    # 2. Fetch dataset
    df = get_unified_media_df(start_date, end_date)
    
    if df is None or df.empty:
        return render_template('program_detail.html', program=decoded_program_name, charts={}, no_data=True, start_date=start_date, end_date=end_date)
    
    # 3. Filter by program name
    df = filter_comma_separated_exact(df, 'programs', decoded_program_name)
    
    if df.empty:
        return render_template('program_detail.html', program=decoded_program_name, charts={}, no_data=True, start_date=start_date, end_date=end_date)
    
    # 4. Standardize media names and weights
    if 'standardize_media_name' in globals():
        df['media_source'] = df['media_source'].apply(standardize_media_name)
    df['weight'] = 1

    platform_link_columns = {
        'Facebook': 'facebook_link',
        'YouTube': 'youtube_link',
        'Instagram': 'instagram_link',
        'Twitter': 'twitter_link',
        'TikTok': 'tiktok_link',
        'Website': 'source_link'
    }
    platform_post_counts = []
    for platform, link_column in platform_link_columns.items():
        if link_column in df.columns:
            has_post_link = df[link_column].fillna('').astype(str).str.strip().ne('')
            post_count = df.loc[has_post_link, 'media_id'].nunique()
        else:
            post_count = 0
        platform_post_counts.append({'platform': platform, 'posts': post_count})

    platform_posts = pd.DataFrame(platform_post_counts)
    fig_platform_posts = px.bar(
        platform_posts, x='platform', y='posts', color='posts',
        title=f"Posts by Media Platform - {decoded_program_name}",
        labels={'platform': 'Media Platform', 'posts': 'Number of Posts'},
        text_auto=True,
        color_continuous_scale='Blues'
    )
    fig_platform_posts.update_layout(
        showlegend=False,
        height=420,
        margin=dict(l=35, r=25, t=55, b=65),
        bargap=0.35,
        xaxis={'automargin': True},
        yaxis={'automargin': True}
    )
    fig_platform_posts.update_traces(textposition='outside', cliponaxis=False)

    # -------------------------------------------------------------------------
    # Chart 1: Reach by Platform in this Program
    # -------------------------------------------------------------------------
    def sum_platform_cols(cols, dframe=df):
        return sum(pd.to_numeric(dframe[c], errors='coerce').fillna(0).sum() for c in cols if c in dframe.columns)

    facebook_eng_cols  = ['facebook_total_engagments']
    youtube_eng_cols   = ['youtube_engagments']
    instagram_eng_cols = ['instagram_engagment']
    twitter_eng_cols   = ['twitter_total_engagment']
    tiktok_eng_cols    = ['tiktok_engagments']
    website_eng_cols   = ['website_engagments']

    social_data = pd.DataFrame([
        {'platform': 'Facebook',  'reach': sum_platform_cols(facebook_eng_cols)},
        {'platform': 'YouTube',   'reach': sum_platform_cols(youtube_eng_cols)},
        {'platform': 'Instagram', 'reach': sum_platform_cols(instagram_eng_cols)},
        {'platform': 'Twitter',   'reach': sum_platform_cols(twitter_eng_cols)},
        {'platform': 'TikTok',    'reach': sum_platform_cols(tiktok_eng_cols)},
        {'platform': 'Website',   'reach': sum_platform_cols(website_eng_cols)}
    ]).sort_values('reach', ascending=False)
    
    y_top = social_data['reach'].max() * 1.15
    fig_platforms = px.bar(
        social_data, 
        x='platform', 
        y='reach', 
        color='reach',
        title=f"Total Reach by Platform - {decoded_program_name}",
        labels={'platform': 'Platform', 'reach': 'Total Engagements'},
        text_auto='.2s',
        color_continuous_scale='Greens'
    )
    fig_platforms.update_layout(
                showlegend=False,
                xaxis_tickangle=-45,
                height=550,
                margin=dict(l=20, r=20, t=40, b=40),
                bargap=0.6,
                title={'font': {'size': 14}},
                xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}},
                yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}}
    )
    fig_platforms.update_traces(width=0.6, textfont={'size': 12}, textposition='outside')

    # -------------------------------------------------------------------------
    # Chart 2: Total Presence per Author in this Program
    # -------------------------------------------------------------------------
    presence_mask = (
        df['programs'].astype(str).str.contains(decoded_program_name, case=False, na=False) & 
        ~df['media_id'].astype(str).str.startswith(('p', 'sm'))
    )
    presence_df = df[presence_mask].copy()
    presence_df = presence_df[
        presence_df['author'].notna() & (presence_df['author'].astype(str).str.strip() != '') &
        presence_df['media_source'].notna() & (presence_df['media_source'].astype(str).str.strip() != '')
    ].copy()

    if not presence_df.empty:
        # Use the same final interview subset for both presence charts so their totals
        # stay aligned for the selected program.
        auth_counts = build_presence_counts(presence_df, 'author', 'author').head(15)
    else:
        auth_counts = pd.DataFrame(columns=['author', 'interviews'])
    
    author_total_count = int(auth_counts['interviews'].sum()) if not auth_counts.empty else 0
    fig_authors = px.bar(
        auth_counts, 
        x='author', 
        y='interviews', 
        color='interviews',
        title=f"Total Presence per Author - {decoded_program_name}",
        labels={'author': 'Author', 'interviews': f'Total Count: {author_total_count}'},
        text_auto=True,
        color_continuous_scale='Greens'
    )
    fig_authors.update_layout(
        showlegend=False,
        xaxis_tickangle=-40,
        height=430,
        margin=dict(l=20, r=20, t=70, b=95),
        bargap=0.6,
        title={'font': {'size': 14}},
        xaxis={'tickfont': {'size': 9}, 'title': {'font': {'size': 10}}, 'automargin': True},
        yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}}
    )
    fig_authors.update_traces(width=0.6, textfont={'size': 10})
    
    if 'add_author_images_to_bar_chart' in globals() and not auth_counts.empty:
        add_author_images_to_bar_chart(fig_authors, auth_counts, image_size_fraction=0.25)
    fig_authors.update_layout(height=430, margin=dict(l=20, r=20, t=70, b=95))

    # -------------------------------------------------------------------------
    # Chart 3: Total Presence per Media Output in this Program
    # -------------------------------------------------------------------------
    media_df = presence_df.copy()
    if not media_df.empty:
        media_counts = build_presence_counts(media_df, 'media_source', 'media').head(15)
    else:
        media_counts = pd.DataFrame(columns=['media', 'interviews'])
    
    media_total_count = int(media_counts['interviews'].sum()) if not media_counts.empty else 0
    fig_media = px.bar(
        media_counts, 
        x='media', 
        y='interviews', 
        color='interviews',
        title=f"Total Presence per Media Output - {decoded_program_name}",
        labels={'media': 'Media Output', 'interviews': f'Total Count: {media_total_count}'},
        text_auto=True,
        color_continuous_scale='YlOrRd'
    )
    fig_media.update_layout(showlegend=False, xaxis_tickangle=-45, bargap=0.6)
    fig_media.update_traces(width=0.6)

    # -------------------------------------------------------------------------
    # Chart 4: Website Reach Performance
    # -------------------------------------------------------------------------
    total_views = pd.to_numeric(df.get('website_views', 0), errors='coerce').fillna(0).sum()
    total_eng = pd.to_numeric(df.get('website_engagments', 0), errors='coerce').fillna(0).sum()
    total_weighted_count = df['weight'].sum()
    average_eng = total_eng / total_weighted_count if total_weighted_count > 0 else 0
    
    website_perf = pd.DataFrame([
        {'Metric': 'Total Website Views', 'Value': total_views},
        {'Metric': 'Total Engagements ', 'Value': total_eng},
        {'Metric': 'Average Engagements', 'Value': average_eng}
    ])
    
    fig_website = px.bar(
        website_perf, 
        x='Metric', 
        y='Value', 
        color='Value',
        title=f"Website Reach Performance - {decoded_program_name}",
        labels={'Value': 'Count', 'Metric': 'Performance Metric'},
        text_auto='.2s',
        color_continuous_scale='Purples'
    )
    fig_website.update_layout(bargap=0.6)
    fig_website.update_traces(width=0.2, textposition='outside', cliponaxis=False)
    
    # Render all charts to HTML strings
    charts = {
        'platforms': pio.to_html(fig_platforms, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'platform_posts': pio.to_html(fig_platform_posts, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'authors': pio.to_html(fig_authors, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'media': pio.to_html(fig_media, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'website_perf': pio.to_html(fig_website, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'performance': build_performance_chart(
            df,
            f"Social Media and Website Views and Engagements - {decoded_program_name}",
            chart_height=430
        )
    }
    
    return render_template(
        'program_detail.html', 
        program=decoded_program_name, 
        charts=charts, 
        no_data=False, 
        start_date=start_date, 
        end_date=end_date
    )

@app.route('/output/<path:output_name>', methods=['GET'])
def output_detail(output_name):
    """Display author presence for a selected media output."""
    start_date, end_date = resolve_filter_dates(request)

    df = get_unified_media_df(start_date, end_date)
    df['media_source'] = df['media_source'].apply(standardize_media_name)
    target_output = standardize_media_name(output_name)
    df = df[df['media_source'] == target_output].copy()

    if df.empty:
        return render_template('media_output_detail.html', output=target_output, charts={}, no_data=True, start_date=start_date, end_date=end_date)

    df['weight'] = 1
    df['weight'] = 1
    auth_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    auth_df = auth_df[auth_df['author'].notna() & (auth_df['author'].astype(str).str.strip() != '')].copy()

    if not auth_df.empty:
        auth_df = auth_df.copy()
        auth_df['author'] = auth_df['author'].astype(str).str.split(',')
        auth_exploded = auth_df.explode('author')
        auth_exploded['author'] = auth_exploded['author'].str.strip()
        auth_exploded = auth_exploded[auth_exploded['author'] != '']
        auth_exploded = auth_exploded.drop_duplicates(subset=['media_id', 'author'])
        auth_counts = auth_exploded.groupby('author')['weight'].sum().reset_index()
        auth_counts.columns = ['author', 'interviews']
        auth_counts = auth_counts.sort_values(by='interviews', ascending=False)
    else:
        auth_counts = pd.DataFrame(columns=['author', 'interviews'])

    author_chart_counts = auth_counts.head(15)
    fig_auth = px.bar(author_chart_counts, x='interviews', y='author', color='interviews',
                      orientation='h',
                      title=f"Top {len(author_chart_counts)} Authors for Media Channel: {target_output}",
                      labels={'author': 'Author', 'interviews': 'Total Interviews'},
                      text_auto=True,
                      color_continuous_scale='Greens')
    fig_auth.update_layout(
        showlegend=False,
        height=max(360, len(author_chart_counts) * 24 + 120),
        yaxis={'categoryorder': 'total ascending', 'automargin': True},
        margin=dict(l=30, r=25, t=60, b=40),
        bargap=0.35
    )
                                                                                                                                                                
    fig_auth.update_traces(textposition='outside', cliponaxis=False)

    program_counts = build_presence_counts(df, 'programs', 'program').head(15)
    category_counts = build_presence_counts(df, 'categories', 'category').head(15)

    def build_channel_presence_chart(counts, label, title, color_scale):
        fig = px.bar(
            counts, x='interviews', y=label, color='interviews',
            orientation='h', title=title,
            labels={label: label.title(), 'interviews': 'Total Presence'},
            text_auto=True, color_continuous_scale=color_scale
        )
        fig.update_layout(
            showlegend=False,
            height=max(360, len(counts) * 24 + 120),
            yaxis={'categoryorder': 'total ascending', 'automargin': True},
            margin=dict(l=30, r=25, t=60, b=40),
            bargap=0.35
        )
        fig.update_traces(textposition='outside', cliponaxis=False)
        return fig

    fig_programs = build_channel_presence_chart(
        program_counts, 'program', f"Top {len(program_counts)} Programs on {target_output}", 'Blues'
    )
    fig_categories = build_channel_presence_chart(
        category_counts, 'category', f"Top {len(category_counts)} Categories on {target_output}", 'Teal'
    )

    charts = {
        'authors': pio.to_html(fig_auth, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'programs': pio.to_html(fig_programs, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'categories': pio.to_html(fig_categories, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'performance': build_performance_chart(
            df, f"Views and Engagements - {target_output}", chart_height=430
        )
    }
    authors_list = auth_counts.to_dict(orient='records')

    return render_template('media_output_detail.html', output=target_output, charts=charts,
                           no_data=False, start_date=start_date, end_date=end_date,
                           authors=authors_list)

@app.route('/api/output_authors/<path:output_name>', methods=['GET'])
def api_output_authors(output_name):
    start_date = request.args.get('start_date', '2020-02-01')
    end_date = request.args.get('end_date', '2026-06-01')

    df = get_unified_media_df(start_date, end_date)
    df['media_source'] = df['media_source'].apply(standardize_media_name)
    target_output = standardize_media_name(output_name)
    df = df[df['media_source'] == target_output].copy()

    if df.empty:
        return jsonify({'output': target_output, 'authors': []})

    # Removed the duplicate df['weight'] = 1 assignment line
    df['weight'] = 1
    auth_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    auth_df = auth_df[auth_df['author'].notna() & (auth_df['author'].astype(str).str.strip() != '')].copy()

    if auth_df.empty:
        return jsonify({'output': target_output, 'authors': []})

    auth_df = auth_df.copy()
    auth_df['author'] = auth_df['author'].astype(str).str.split(',')
    auth_exploded = auth_df.explode('author')
    auth_exploded['author'] = auth_exploded['author'].str.strip()
    auth_exploded = auth_exploded[auth_exploded['author'] != '']
    auth_exploded = auth_exploded.drop_duplicates(subset=['media_id', 'author'])

    auth_counts = auth_exploded.groupby('author')['weight'].sum().reset_index()
    auth_counts.columns = ['author', 'interviews']
    auth_counts = auth_counts.sort_values(by='interviews', ascending=False)

    # Convert to records dict list
    raw_authors = auth_counts.to_dict(orient='records')
    
    # --- EDITED SECTION: Inject dynamic media paths and routing parameters ---
    formatted_authors = []
    for item in raw_authors:
        name = item['author']
        
        # Get filename using your helper function or fall back to default avatar
        photo_filename = get_author_photo_filename(name) or 'default_avatar.png'
        
        formatted_authors.append({
            'name': name,
            'interviews': int(item['interviews']),
            'image_url': url_for('author_image', filename=photo_filename),
            'profile_url': url_for('author_detail', author_name=name)
        })
    # -------------------------------------------------------------------------

    return jsonify({'output': target_output, 'authors': formatted_authors})

@app.route('/category/<path:category_name>', methods=['GET'])
def category_detail(category_name):
    """Display detailed analysis for a specific category"""
    decoded_category_name = unquote(category_name)
    start_date, end_date = resolve_filter_dates(request)
    
    # 1. Fetch dataset
    df = get_unified_media_df(start_date, end_date)
    
    if df is None or df.empty:
        return render_template('category_detail.html', category=decoded_category_name, charts={}, no_data=True, start_date=start_date, end_date=end_date)
    
    # Filter by category name
    df = df[df['categories'].astype(str).str.contains(decoded_category_name, case=False, na=False)].copy()
    
    if df.empty:
        return render_template('category_detail.html', category=decoded_category_name, charts={}, no_data=True, start_date=start_date, end_date=end_date)
    
    if 'standardize_media_name' in globals():
        df['media_source'] = df['media_source'].apply(standardize_media_name)
    df['weight'] = 1

    # -------------------------------------------------------------------------
    # Chart 1: Reach by Platform
    # -------------------------------------------------------------------------
    def sum_platform_cols(cols, dframe=df):
        return sum(pd.to_numeric(dframe[c], errors='coerce').fillna(0).sum() for c in cols if c in dframe.columns)

    facebook_eng_cols  = ['facebook_total_engagments']
    youtube_eng_cols   = ['youtube_engagments']
    instagram_eng_cols = ['instagram_engagment']
    twitter_eng_cols   = ['twitter_total_engagment']
    tiktok_eng_cols    = ['tiktok_engagments']
    website_eng_cols   = ['website_engagments']

    social_data = pd.DataFrame([
        {'platform': 'Facebook',  'reach': sum_platform_cols(facebook_eng_cols)},
        {'platform': 'YouTube',   'reach': sum_platform_cols(youtube_eng_cols)},
        {'platform': 'Instagram', 'reach': sum_platform_cols(instagram_eng_cols)},
        {'platform': 'Twitter',   'reach': sum_platform_cols(twitter_eng_cols)},
        {'platform': 'TikTok',    'reach': sum_platform_cols(tiktok_eng_cols)},
        {'platform': 'Website',   'reach': sum_platform_cols(website_eng_cols)}
    ]).sort_values('reach', ascending=False)
    
    fig_platforms = px.bar(
        social_data, x='platform', y='reach', color='reach',
        title=f"Total Reach by Platform - {decoded_category_name}",
        labels={'platform': 'Platform', 'reach': 'Total Engagements'},
        text_auto='.2s', color_continuous_scale='Blues'
    )
    fig_platforms.update_layout(
        showlegend=False, xaxis_tickangle=-45, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6,
        title={'font': {'size': 14}},
        xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}},
        yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}}
    )
    fig_platforms.update_traces(width=0.6, textfont={'size': 12})

    # Base dataset for Author and Media counts (excluding 'p' and 'sm')
    valid_base = df[
        df['categories'].astype(str).str.contains(decoded_category_name, case=False, na=False) & 
        ~df['media_id'].astype(str).str.startswith(('p', 'sm'))
    ].copy()

    # -------------------------------------------------------------------------
    # Chart 2: Total Presence per Author
    # -------------------------------------------------------------------------
    presence_df = valid_base[
        valid_base['author'].notna() & (valid_base['author'].astype(str).str.strip() != '') &
        valid_base['media_source'].notna() & (valid_base['media_source'].astype(str).str.strip() != '')
    ].copy()
    if not presence_df.empty:
        # Use the same valid interview subset for author and media totals so they
        # always align for the selected category.
        auth_counts = build_presence_counts(presence_df, 'author', 'author').head(15)
    else:
        auth_counts = pd.DataFrame(columns=['author', 'interviews'])
    
    author_total_count = int(auth_counts['interviews'].sum()) if not auth_counts.empty else 0
    fig_authors = px.bar(
        auth_counts, x='author', y='interviews', color='interviews',
        title=f"Total Presence per Author - {decoded_category_name}",
        labels={'author': 'Author', 'interviews': f'Total Count: {author_total_count}'},
        text_auto=True, color_continuous_scale='Greens'
    )
    fig_authors.update_layout(
        showlegend=False, xaxis_tickangle=-45, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6,
        title={'font': {'size': 14}},
        xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}},
        yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}}
    )
    fig_authors.update_traces(width=0.6, textposition='outside', textfont={'size': 12})
    
    if 'add_author_images_to_bar_chart' in globals() and not auth_counts.empty:
        add_author_images_to_bar_chart(fig_authors, auth_counts)

    # -------------------------------------------------------------------------
    # Chart 3: Total Presence per Media Output
    # -------------------------------------------------------------------------
    media_df = presence_df.copy()
    if not media_df.empty:
        media_counts = build_presence_counts(media_df, 'media_source', 'media').head(15)
    else:
        media_counts = pd.DataFrame(columns=['media', 'interviews'])
    
    media_total_count = int(media_counts['interviews'].sum()) if not media_counts.empty else 0
    fig_media = px.bar(
        media_counts, x='interviews', y='media', color='interviews',
        orientation='h',
        title=f"Total Presence per Media Output - {decoded_category_name}",
        labels={'media': 'Media Output', 'interviews': f'Total Count: {media_total_count}'},
        text_auto=True, color_continuous_scale='YlOrRd'
    )
    fig_media.update_layout(
        showlegend=False,
        height=600,
        margin=dict(l=30, r=25, t=60, b=40),
        bargap=0.35,
        title={'font': {'size': 14}},
        xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}},
        yaxis={
            'categoryorder': 'total ascending',
            'automargin': True,
            'tickfont': {'size': 10},
            'title': {'font': {'size': 11}}
        }
    )
    fig_media.update_traces(textposition='outside', textfont={'size': 12}, cliponaxis=False)

    # -------------------------------------------------------------------------
    # Chart 4: Website Performance
    # -------------------------------------------------------------------------
    total_views = pd.to_numeric(df.get('website_views', 0), errors='coerce').fillna(0).sum()
    total_eng = pd.to_numeric(df.get('website_engagments', 0), errors='coerce').fillna(0).sum()
    total_weighted_count = df['weight'].sum()
    average_eng = total_eng / total_weighted_count if total_weighted_count > 0 else 0
    
    website_perf = pd.DataFrame([
        {'Metric': 'Total Website Views', 'Value': total_views},
        {'Metric': 'Total Engagements ', 'Value': total_eng},
        {'Metric': 'Average Engagements', 'Value': average_eng}
    ])
    
    fig_website = px.bar(
        website_perf, x='Metric', y='Value', color='Value',
        title=f"Website Reach Performance - {decoded_category_name}",
        labels={'Value': 'Count', 'Metric': 'Performance Metric'},
        text_auto='.2s', color_continuous_scale='Purples'
    )
    fig_website.update_layout(bargap=0.6)
    fig_website.update_traces(width=0.2, textposition='outside', cliponaxis=False)
    
    charts = {
        'platforms': pio.to_html(fig_platforms, full_html=False, include_plotlyjs='cdn'),
        'authors': pio.to_html(fig_authors, full_html=False, include_plotlyjs='cdn'),
        'media': pio.to_html(fig_media, full_html=False, include_plotlyjs='cdn'),
        'website_perf': pio.to_html(fig_website, full_html=False, include_plotlyjs='cdn'),
        'performance': build_performance_chart(df, f"Social Media and Website Views and Engagements - {decoded_category_name}")
    }
    
    return render_template('category_detail.html', category=decoded_category_name, charts=charts, no_data=False, start_date=start_date, end_date=end_date)


@app.route('/author/<path:author_name>', methods=['GET'])
def author_detail(author_name):
    """Display detailed analysis for a specific author"""
    start_date, end_date = resolve_filter_dates(request)

    df = get_unified_media_df(start_date, end_date)
    # Filter rows where the author appears
    df = filter_comma_separated_exact(df, 'author', author_name)

    author_photo = get_author_photo_filename(author_name)

    if df.empty:
        return render_template('author_detail.html', author=author_name, charts={}, no_data=True, start_date=start_date, end_date=end_date, author_photo=author_photo)

    # Normalize and prepare
    df['media_source'] = df['media_source'].apply(standardize_media_name)
    df['weight'] = 1

    # Chart 1: Interviews per Program for this Author
    prog_counts = build_presence_counts(df, 'programs', 'program')

    prog_total_count = int(prog_counts['interviews'].sum()) if not prog_counts.empty else 0
    fig_prog = px.bar(prog_counts, x='interviews', y='program', color='interviews',
                     orientation='h',
                     custom_data=['program'],
                     title=f"Programs - Interviews for {author_name}",
                     labels={'program': 'Program Name', 'interviews': f'Total Count: {prog_total_count}'},
                     text_auto=True,
                     color_continuous_scale='Blues')
    fig_prog.update_layout(
        showlegend=False,
        height=max(420, len(prog_counts) * 28 + 120),
        yaxis={'categoryorder': 'total ascending', 'automargin': True},
        margin=dict(l=30, r=25, t=55, b=35),
        bargap=0.35
    )
    fig_prog.update_traces(width=0.6, textposition='outside', cliponaxis=False)

    # Chart 2: Interviews per Media Output for this Author
    all_media_counts = build_presence_counts(df, 'media_source', 'media')
    top_media_counts = all_media_counts.head(15) if not all_media_counts.empty else pd.DataFrame(columns=['media', 'interviews'])
    media_show_more = len(all_media_counts) > 15 if not all_media_counts.empty else False

    # Preview Media Output Chart (Top 15)
    media_preview_total_count = int(top_media_counts['interviews'].sum()) if not top_media_counts.empty else 0
    fig_media_preview = px.bar(top_media_counts, x='media', y='interviews', color='interviews',
                      title=f"Media Outputs - Interviews for {author_name}",
                      labels={'media': 'Media Output', 'interviews': f'Total Count: {media_preview_total_count}'},
                      text_auto=True,
                      color_continuous_scale='YlOrRd')
    fig_media_preview.update_layout(showlegend=False, xaxis_tickangle=-45, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6)
    fig_media_preview.update_traces(width=0.6)

    # Full Media Output Chart (All outlets, hidden by default)
    chart_width_media = max(1200, len(all_media_counts) * 40)
    media_all_total_count = int(all_media_counts['interviews'].sum()) if not all_media_counts.empty else 0
    fig_media_all = px.bar(all_media_counts, x='media', y='interviews', color='interviews',
                      title=f"Media Outputs - Interviews for {author_name} (All)",
                      labels={'media': 'Media Output', 'interviews': f'Total Count: {media_all_total_count}'},
                      text_auto=True,
                      color_continuous_scale='YlOrRd',
                      width=chart_width_media)
    fig_media_all.update_layout(showlegend=False, xaxis_tickangle=-45, bargap=0.6, xaxis={'automargin': True})
    fig_media_all.update_traces(width=0.6)

    # Chart 3: Output Types for this Author
    out_counts = build_presence_counts(df, 'output', 'category')
    out_counts = out_counts.rename(columns={'category': 'category', 'interviews': 'count'})

    fig_out = px.bar(out_counts, x='category', y='count', color='category',
                    title=f"Output Types - {author_name}",
                    labels={'category': 'Output Category', 'count': 'Quantity'},
                    text_auto='.2s',
                    color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_out.update_layout(showlegend=False, legend_title="Output Types", margin=dict(l=20, r=20, t=40, b=40), bargap=0.6)
    fig_out.update_traces(width=0.6, textposition='outside', cliponaxis=False)

    category_counts = build_presence_counts(df, 'categories', 'category')
    top_category_counts = category_counts.head(10)
    category_show_more = len(category_counts) > 10

    def build_category_chart(counts):
        fig = px.bar(
            counts, x='interviews', y='category', color='interviews',
            orientation='h',
            title=f"Categories - Interviews for {author_name}",
            labels={'category': 'Category', 'interviews': 'Number of Interviews'},
            text_auto=True,
            color_continuous_scale='Teal'
        )
        fig.update_layout(
            showlegend=False,
            height=max(420, len(counts) * 28 + 120),
            yaxis={'categoryorder': 'total ascending', 'automargin': True},
            margin=dict(l=30, r=25, t=55, b=35),
            bargap=0.35
        )
        fig.update_traces(textposition='outside', cliponaxis=False)
        return fig

    fig_categories_preview = build_category_chart(top_category_counts)
    fig_categories_all = build_category_chart(category_counts)

    charts = {
        'programs': pio.to_html(fig_prog, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'media_preview': pio.to_html(fig_media_preview, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'media_all': pio.to_html(fig_media_all, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'outputs': pio.to_html(fig_out, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'categories_preview': pio.to_html(fig_categories_preview, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'categories_all': pio.to_html(fig_categories_all, full_html=False, include_plotlyjs='cdn', config={'responsive': True}),
        'performance': build_performance_chart(df, f"Social Media and Website Views and Engagements - {author_name}")
    }

    return render_template('author_detail.html', author=author_name, charts=charts, no_data=False, start_date=start_date, end_date=end_date, author_photo=author_photo, media_show_more=media_show_more, category_show_more=category_show_more)

@app.route('/programs')
def programs_list():
    """Get list of all programs for the selector"""
    conn = get_db_connection()
    query = """
    SELECT DISTINCT media_program AS programs FROM media_programs WHERE media_program IS NOT NULL AND media_program != ''
    UNION
    SELECT DISTINCT part_program_name AS programs FROM parts_programs WHERE part_program_name IS NOT NULL AND part_program_name != ''
    """
    result = pd.read_sql_query(query, conn)
    conn.close()
    
    programs = []
    for prog_str in result['programs']:
        if prog_str and str(prog_str).strip():
            # Split comma-separated programs
            for prog in str(prog_str).split(','):
                prog = prog.strip().upper()
                # Filter out media keywords
                if prog and prog not in MEDIA_KEYWORDS and prog not in programs:
                    programs.append(prog)
    
    programs.sort()
    return {'programs': programs}

@app.route('/categories')
def categories_list():
    """Get list of all categories for the selector"""
    conn = get_db_connection()
    query = "SELECT DISTINCT media_category AS categories FROM media_categories WHERE media_category IS NOT NULL AND media_category != ''"
    result = pd.read_sql_query(query, conn)
    conn.close()
    
    categories = []
    for cat_str in result['categories']:
        if cat_str and str(cat_str).strip():
            # Split comma-separated categories
            for cat in str(cat_str).split(','):
                cat = cat.strip().upper()
                if cat and cat not in categories:
                    categories.append(cat)
    
    categories.sort()
    return {'categories': categories}

@app.route('/output-type/<path:output_type>')
def output_type_details(output_type):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Query 1: Authors who interviewed under this Output Type
    authors_query = """
        SELECT author, COUNT(*) as interview_count
        FROM media_kpis
        WHERE output_type = %s
          AND (%s::date IS NULL OR date >= %s::date)
          AND (%s::date IS NULL OR date <= %s::date)
        GROUP BY author
        ORDER BY interview_count DESC
    """
    
    # Query 2: Programs broadcasted under this Output Type
    programs_query = """
        SELECT program, COUNT(*) as program_count
        FROM media_kpis
        WHERE output_type = %s
          AND (%s::date IS NULL OR date >= %s::date)
          AND (%s::date IS NULL OR date <= %s::date)
        GROUP BY program
        ORDER BY program_count DESC
    """

    authors = db.execute(authors_query, (output_type, start_date, start_date, end_date, end_date)).fetchall()
    programs = db.execute(programs_query, (output_type, start_date, start_date, end_date, end_date)).fetchall()

    return render_template('output_type_details.html', 
                           output_type=output_type, 
                           authors=authors, 
                           programs=programs)

@app.route('/media-authors/<path:media_name>')
def media_authors(media_name):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Query authors for this specific media output
    # (Adjust table/column names to match your schema, e.g., media_kpis or media_output)
    query = """
        SELECT author, COUNT(*) as total_interviews 
        FROM media_kpis 
        WHERE media_output = %s
    """
    params = [media_name]

    if start_date and end_date:
        query += " AND date BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    query += " GROUP BY author ORDER BY total_interviews DESC"

    # Fetch records and pass to template
    authors = db.execute(query, params).fetchall()

    return render_template('media_authors.html', media_name=media_name, authors=authors)

@app.route('/output/<path:media_name>')
def media_output_page(media_name):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Query database to get unique authors for this media platform
    authors = db.execute("""
        SELECT author, COUNT(*) as interview_count
        FROM media_kpis
        WHERE media_output = %s
          AND (%s::date IS NULL OR date >= %s::date)
          AND (%s::date IS NULL OR date <= %s::date)
        GROUP BY author
        ORDER BY interview_count DESC
    """, (media_name, start_date, start_date, end_date, end_date)).fetchall()

    return render_template('output_details.html', media_name=media_name, authors=authors)

@app.route('/authors')
def authors_list():
    """Get list of all authors for the selector"""
    conn = get_db_connection()
    result = pd.read_sql_query(
        "SELECT DISTINCT author_name AS author FROM media_authors WHERE author_name IS NOT NULL AND BTRIM(author_name) <> ''",
        conn
    )
    conn.close()

    authors = []
    for auth_str in result['author'].dropna().unique():
        for author in str(auth_str).split(','):
            author = author.strip()
            if author and author not in authors:
                authors.append(author)
    authors = sorted(authors)
    return {'authors': authors}


def parse_duration(duration_str):
    """Convert HH:MM:SS string to total seconds"""
    if not duration_str or not isinstance(duration_str, str):
        return 0
    try:
        parts = duration_str.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except:
        return 0

@app.route('/media', methods=['GET', 'POST'])
def media_analytics():
    """Display specialized website performance analytics"""
    start_date, end_date = resolve_filter_dates(request)

    df = get_unified_media_df(start_date, end_date)
    df = df[['media_id', 'website_views', 'website_average_duration', 'web_total_users', 'website_engagments', 'date']].copy()

    if df.empty:
        return render_template('media.html', charts={}, start_date=start_date, end_date=end_date, no_data=True)

    # Convert columns to numeric
    df['website_views'] = pd.to_numeric(df['website_views'], errors='coerce').fillna(0)
    df['web_total_users'] = pd.to_numeric(df['web_total_users'], errors='coerce').fillna(0)
    df['website_engagments'] = pd.to_numeric(df['website_engagments'], errors='coerce').fillna(0)
    df['duration_seconds'] = df['website_average_duration'].apply(parse_duration)

    # --- Chart 1: Website Views (Using website_views column) ---
    total_views = df['website_views'].sum()
    avg_views = df['website_views'].mean()
    
    views_data = pd.DataFrame([
        {'Metric': 'Total Website Views', 'Value': total_views, 'Type': 'Total'},
        {'Metric': 'Average Website Views', 'Value': avg_views, 'Type': 'Average'}
    ])
    
    fig_views = px.bar(views_data, x='Metric', y='Value', color='Type',
                       title="Website Views: Total vs Average",
                       labels={'Value': 'Count', 'Metric': 'Metric'},
                       text_auto='.2s',
                       color_discrete_map={'Total': '#6610f2', 'Average': '#a370f7'})
    fig_views.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6)
    fig_views.update_traces(width=0.6, textposition='outside', cliponaxis=False)

    # --- Chart 2: Website Duration (Total vs Average in Seconds) ---
    total_duration = df['duration_seconds'].sum()
    avg_duration = df['duration_seconds'].mean()
    
    duration_data = pd.DataFrame([
        {'Metric': 'Total Duration (Sum of Averages)', 'Value': total_duration, 'Type': 'Total'},
        {'Metric': 'Average Duration', 'Value': avg_duration, 'Type': 'Average'}
    ])
    
    fig_duration = px.bar(duration_data, x='Metric', y='Value', color='Type',
                         title="Website Duration (Seconds): Total vs Average",
                         labels={'Value': 'Seconds', 'Metric': 'Metric'},
                         text_auto='.1f',
                         color_discrete_map={'Total': '#fd7e14', 'Average': '#feb272'})
    fig_duration.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6)
    fig_duration.update_traces(width=0.6)

    # --- Chart 3: Website Users (Total vs Average) ---
    total_users = df['web_total_users'].sum()
    avg_users = df['web_total_users'].mean()
    
    users_data = pd.DataFrame([
        {'Metric': 'Total Unique Users', 'Value': total_users, 'Type': 'Total'},
        {'Metric': 'Average Unique Users', 'Value': avg_users, 'Type': 'Average'}
    ])
    
    fig_users = px.bar(users_data, x='Metric', y='Value', color='Type',
                      title="Website Users: Total vs Average",
                      labels={'Value': 'Count', 'Metric': 'Metric'},
                      text_auto='.2s',
                      color_discrete_map={'Total': '#20c997', 'Average': '#7ee3c8'})
    fig_users.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6)
    fig_users.update_traces(width=0.6)

    # --- Chart 4: Website Engagements (Total vs Average) ---
    df['eng_count'] = df['website_engagments']
    total_eng = df['eng_count'].sum()
    avg_eng = df['eng_count'].mean()
    
    eng_data = pd.DataFrame([
        {'Metric': 'Total Engagements', 'Value': total_eng, 'Type': 'Total'},
        {'Metric': 'Average Engagements', 'Value': avg_eng, 'Type': 'Average'}
    ])
    
    fig_eng = px.bar(eng_data, x='Metric', y='Value', color='Type',
                     title="Website Engagements: Total vs Average",
                     labels={'Value': 'Count', 'Metric': 'Metric'},
                     text_auto='.2s',
                     color_discrete_map={'Total': '#e83e8c', 'Average': '#f06595'})
    fig_eng.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6)
    fig_eng.update_traces(width=0.6)

    charts = {
        'views': pio.to_html(fig_views, full_html=False, include_plotlyjs='cdn'),
        'duration': pio.to_html(fig_duration, full_html=False, include_plotlyjs='cdn'),
        'users': pio.to_html(fig_users, full_html=False, include_plotlyjs='cdn'),
        'engagements': pio.to_html(fig_eng, full_html=False, include_plotlyjs='cdn')
    }
    website_summary = pd.DataFrame([
        {'Metric': 'Website Views', 'Value': total_views},
        {'Metric': 'Website Engagements', 'Value': total_eng},
        {'Metric': 'Unique Users', 'Value': total_users},
        {'Metric': 'Average Duration (seconds)', 'Value': avg_duration}
    ])
    fig_website_summary = px.bar(
        website_summary, x='Metric', y='Value', color='Metric',
        title='Website Performance Summary', text_auto='.2s',
        labels={'Metric': 'Website Metric', 'Value': 'Value'},
        color_discrete_sequence=['#087f8c', '#e76f51', '#2a9d8f', '#f4a261']
    )
    fig_website_summary.update_layout(showlegend=False, height=560, bargap=0.25, margin=dict(l=25, r=25, t=60, b=80))
    fig_website_summary.update_traces(textposition='outside', cliponaxis=False)
    charts['summary'] = pio.to_html(fig_website_summary, full_html=False, include_plotlyjs='cdn')

    return render_template('media.html', charts=charts, start_date=start_date, end_date=end_date, no_data=False)


@app.route('/social/<platform>', methods=['GET', 'POST'])
def social_analytics(platform):
    """Display specialized social media platform analytics"""
    start_date, end_date = resolve_filter_dates(request)

    # Column mapping based on platform
    platform_map = {
        'YouTube': {
            'views': 'youtube_views',
            'likes': 'youtube_likes',
            'comments': 'youtube_engagments',
            'comment_label': 'Total Engagements',
            'post_link': 'youtube_link'
        },
        'Facebook': {
            'views': 'facebook_views',
            'likes': 'facebook_positive_engagment',
            'comments': 'facebook_total_engagments',
            'comment_label': 'Total Engagements',
            'post_link': 'facebook_link'
        },
        'Twitter': {
            'views': 'twitter_impressions',
            'likes': 'twitter_likes',
            'comments': 'twitter_total_engagment',
            'comment_label': 'Total Engagements',
            'post_link': 'twitter_link'
        },
        'Instagram': {
            'views': 'insta_views',
            'likes': 'instagram_engagment',
            'comments': None,
            'comment_label': 'Engagements',
            'post_link': 'instagram_link'
        },
        'TikTok': {
            'views': 'tiktok_views',
            'likes': 'tiktok_engagments',
            'comments': None,
            'comment_label': 'Engagements',
            'post_link': 'tiktok_link'
        }
    }

    if platform not in platform_map:
        return "Platform not supported", 404

    metrics = platform_map[platform]
    
    selected_cols = [metrics['views'], metrics['likes']]
    if metrics['comments']:
        selected_cols.append(metrics['comments'])
        
    df = get_unified_media_df(start_date, end_date)
    breakdown_fields = ['programs', 'author', 'categories']
    post_link_col = metrics['post_link']
    cols_to_keep = list(dict.fromkeys(
        [c for c in selected_cols if c] + [post_link_col, 'media_id', 'date'] + breakdown_fields
    ))
    df = df[cols_to_keep].copy()

    if df.empty:
        return render_template('social_detail.html', platform=platform, charts={}, start_date=start_date, end_date=end_date, no_data=True)

    # Convert to numeric
    for col in selected_cols:
        if col:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- Chart 1: Views (Total vs Average) ---
    v_col = metrics['views']
    total_views = df[v_col].sum()
    # Average only over rows that actually have data for this platform
    avg_views = df.loc[df[v_col] > 0, v_col].mean() if (df[v_col] > 0).any() else 0
    
    views_data = pd.DataFrame([
        {'Metric': 'Total Views', 'Value': total_views, 'Type': 'Total'},
        {'Metric': 'Average Views', 'Value': avg_views, 'Type': 'Average'}
    ])
    
    fig_views = px.bar(views_data, x='Metric', y='Value', color='Type',
                       title=f"{platform} Views: Total vs Average",
                       labels={'Value': 'Count', 'Metric': 'Metric'},
                       text_auto='.2s',
                       color_discrete_map={'Total': '#0d6efd', 'Average': '#7cb5ec'})
    fig_views.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6)
    fig_views.update_traces(width=0.2, textposition='outside', cliponaxis=False)

    # --- Chart 2: Likes (Total vs Average) ---
    l_col = metrics['likes']
    total_likes = df[l_col].sum()
    avg_likes = df.loc[df[l_col] > 0, l_col].mean() if (df[l_col] > 0).any() else 0
    
    likes_data = pd.DataFrame([
        {'Metric': 'Total Likes/Eng.', 'Value': total_likes, 'Type': 'Total'},
        {'Metric': 'Average Likes/Eng.', 'Value': avg_likes, 'Type': 'Average'}
    ])
    
    fig_likes = px.bar(likes_data, x='Metric', y='Value', color='Type',
                      title=f"{platform} Likes/Positive Engagement: Total vs Average",
                      labels={'Value': 'Count', 'Metric': 'Metric'},
                      text_auto='.2s',
                      color_discrete_map={'Total': '#198754', 'Average': '#75b798'})
    fig_likes.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6)
    fig_likes.update_traces(width=0.2)

    # --- Chart 3: Comments/Engagements (Total vs Average) ---
    c_col = metrics['comments']
    if c_col:
        total_comments = df[c_col].sum()
        avg_comments = df.loc[df[c_col] > 0, c_col].mean() if (df[c_col] > 0).any() else 0
        label = metrics['comment_label']
    else:
        # Fallback for platforms without a separate comments column
        total_comments = total_likes
        avg_comments = avg_likes
        label = metrics['comment_label']
    
    comments_data = pd.DataFrame([
        {'Metric': f'Total {label}', 'Value': total_comments, 'Type': 'Total'},
        {'Metric': f'Average {label}', 'Value': avg_comments, 'Type': 'Average'}
    ])
    
    fig_comments = px.bar(comments_data, x='Metric', y='Value', color='Type',
                        title=f"{platform} {label}: Total vs Average",
                        labels={'Value': 'Count', 'Metric': 'Metric'},
                        text_auto='.2s',
                        color_discrete_map={'Total': '#ffc107', 'Average': '#ffda6a'})
    fig_comments.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=40), bargap=0.6)
    fig_comments.update_traces(width=0.2)

    charts = {
        'views': pio.to_html(fig_views, full_html=False, include_plotlyjs='cdn'),
        'likes': pio.to_html(fig_likes, full_html=False, include_plotlyjs='cdn'),
        'comments': pio.to_html(fig_comments, full_html=False, include_plotlyjs='cdn')
    }

    engagement_col = metrics['comments'] or metrics['likes']
    breakdown_specs = [
        ('programs', 'Programs'),
        ('author', 'Authors'),
        ('categories', 'Categories')
    ]
    metric_specs = [
        ('views', '#0d6efd'),
        ('engagement', '#198754'),
        ('posts', '#fd7e14')
    ]

    for field, breakdown_label in breakdown_specs:
        breakdown = df[['media_id', field, v_col, engagement_col, post_link_col]].copy()
        breakdown[field] = breakdown[field].fillna('').astype(str).str.split(',')
        breakdown = breakdown.explode(field)
        breakdown[field] = breakdown[field].astype(str).str.strip()
        breakdown = breakdown[breakdown[field].ne('') & breakdown[field].str.casefold().ne('nan')]
        breakdown = breakdown.drop_duplicates(subset=['media_id', field])
        breakdown['posts'] = breakdown[post_link_col].fillna('').astype(str).str.strip().ne('').astype(int)

        counts = breakdown.groupby(field, as_index=False).agg(
            views=(v_col, 'sum'),
            engagement=(engagement_col, 'sum'),
            posts=('posts', 'sum')
        )
        counts = counts.sort_values(['views', 'engagement', 'posts'], ascending=False).head(15)

        fig_breakdown = make_subplots(
            rows=1,
            cols=3,
            shared_yaxes=True,
            subplot_titles=('Views', 'Engagements', 'Posts')
        )
        for column_index, (column, color) in enumerate(metric_specs, start=1):
            values = counts[column]
            fig_breakdown.add_trace(
                go.Bar(
                    x=values,
                    y=counts[field],
                    orientation='h',
                    marker_color=color,
                    text=values,
                    texttemplate='%{text:,.0f}',
                    textposition='outside',
                    cliponaxis=False,
                    name=column.title(),
                    showlegend=False
                ),
                row=1,
                col=column_index
            )

        figure_height = max(380, len(counts) * 28 + 150)
        fig_breakdown.update_layout(
            title=f'{breakdown_label} on {platform} (Top {len(counts)})',
            height=figure_height,
            margin=dict(l=25, r=35, t=80, b=35),
            bargap=0.3
        )
        fig_breakdown.update_yaxes(
            categoryorder='total ascending',
            automargin=True,
            tickfont={'size': 10}
        )
        fig_breakdown.update_xaxes(
            automargin=True,
            tickfont={'size': 9},
            title_font={'size': 10}
        )
        charts[field] = pio.to_html(
            fig_breakdown, full_html=False, include_plotlyjs='cdn', config={'responsive': True}
        )

    social_summary = pd.DataFrame([
        {'Metric': 'Views', 'Value': total_views},
        {'Metric': 'Likes / Engagement', 'Value': total_likes},
        {'Metric': label, 'Value': total_comments}
    ])
    fig_social_summary = px.bar(
        social_summary, x='Metric', y='Value', color='Metric',
        title=f'{platform} Performance Summary', text_auto='.2s',
        labels={'Metric': 'Metric', 'Value': 'Value'},
        color_discrete_sequence=['#087f8c', '#f4a261', '#e76f51']
    )
    fig_social_summary.update_layout(showlegend=False, height=560, bargap=0.25, margin=dict(l=25, r=25, t=60, b=80))
    fig_social_summary.update_traces(textposition='outside', cliponaxis=False)
    charts['summary'] = pio.to_html(fig_social_summary, full_html=False, include_plotlyjs='cdn')

    return render_template('social_detail.html', platform=platform, charts=charts, start_date=start_date, end_date=end_date, no_data=False)


@app.route('/preview')
def data_preview():
    # List of columns to select in the specified order
    columns_to_show = [
        'media_id', 'title', 'title_english', 'output', 'website_views', 
        'website_average_duration', 'web_total_users', 'website_engagments', 
        'date', 'author', 'media_source', 'source_link', 'source_youtube_views', 
        'source_likes_youtube', 'source_youtube_comments', 'programs', 
        'categories', 'tags', 'whatsapp_sent', 'youtube_link', 'youtube_date', 
        'youtube_views', 'youtube_engagments', 'youtube_watch_time', 'status', 
        'facebook_link', 'facebook_views', 'facebook_total_engagments', 
        'facebook_positive_engagment', 'instagram_link', 'insta_views', 
        'instagram_engagment', 'twitter_link', 'twitter_impressions', 
        'twitter_total_engagment', 'tiktok_link', 'tiktok_views', 
        'tiktok_engagments', 'copies'
    ]
    
    # Mapping for display names
    display_names = {
        'media_id': '#',
        'title': 'Title',
        'title_english': 'English Title',
        'output': 'Output',
        'website_views': 'Website Views',
        'website_average_duration': 'Website',
        'web_total_users': 'Website total users',
        'website_engagments': 'Website engagements',
        'date': 'Date',
        'author': 'Expert',
        'media_source': 'Media',
        'source_link': 'Source link',
        'source_youtube_views': 'Source views (youtube)',
        'source_likes_youtube': 'Source likes (youtube)',
        'source_youtube_comments': 'Source comments (youtube)',
        'programs': 'Program',
        'categories': 'Categories',
        'tags': 'Tags',
        'whatsapp_sent': 'Whatsapp sent',
        'youtube_link': 'Youtube link',
        'youtube_date': 'Youtube date',
        'youtube_views': 'Youtube Views',
        'youtube_engagments': 'Youtube Engagements',
        'youtube_watch_time': 'Youtube Watch Time',
        'status': 'Status',
        'facebook_link': 'Facebook link',
        'facebook_views': 'FB Views',
        'facebook_total_engagments': 'FB Total engagements',
        'facebook_positive_engagment': 'FB Positive engagements',
        'instagram_link': 'Instagram link',
        'insta_views': 'Instagram Views',
        'instagram_engagment': 'Instagram Engagements',
        'twitter_link': 'Twitter link',
        'twitter_impressions': 'Twitter impressions',
        'twitter_total_engagment': 'Twitter total engagement',
        'tiktok_link': 'Tiktok link',
        'tiktok_views': 'Tiktok Views',
        'tiktok_engagments': 'Tiktok Engagements',
        'copies': 'Copies'
    }
    
    df = get_unified_media_df('2000-01-01', '2100-01-01')
    df = df[columns_to_show].sort_values(by=['date', 'media_id'], ascending=[False, False]).head(1000).copy()
    
    # Rename columns for display
    df = df.rename(columns=display_names)
    
    # Add an Empty Edit column at the end
    df['Edit'] = ''
    
    # Generate HTML table
    table_html = df.to_html(classes="table table-hover table-striped table-sm", index=False, border=0)
    
    # Get date range from query parameters (if any) or use defaults
    start_date = request.args.get('start_date', '2020-02-01')
    end_date = request.args.get('end_date', '2026-06-01')
    
    return render_template('preview.html', table_html=table_html, start_date=start_date, end_date=end_date)

if __name__ == '__main__':
    app.run(debug=True, port=5000)