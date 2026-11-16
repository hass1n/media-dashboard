from flask import Flask, request
import pandas as pd

from app import build_presence_counts, resolve_filter_dates, build_home_dashboard_charts


def test_resolve_filter_dates_prefers_query_string():
    app = Flask(__name__)
    with app.test_request_context('/?start_date=2024-01-01&end_date=2024-02-01'):
        assert resolve_filter_dates(request) == ('2024-01-01', '2024-02-01')


def test_resolve_filter_dates_falls_back_to_form_values():
    app = Flask(__name__)
    with app.test_request_context('/', method='POST', data={'start_date': '2024-03-01', 'end_date': '2024-04-01'}):
        assert resolve_filter_dates(request) == ('2024-03-01', '2024-04-01')


def test_build_presence_counts_splits_multi_value_fields():
    df = pd.DataFrame([
        {'media_id': 'm1', 'author': 'Alice, Bob', 'programs': 'Program A', 'media_source': 'CNN', 'output': 'TV', 'weight': 1},
        {'media_id': 'm2', 'author': 'Alice', 'programs': 'Program A, Program B', 'media_source': 'BBC', 'output': 'Radio', 'weight': 1},
    ])

    author_counts = build_presence_counts(df, 'author', 'author')
    assert author_counts.to_dict('records') == [
        {'author': 'Alice', 'interviews': 2},
        {'author': 'Bob', 'interviews': 1},
    ]

    program_counts = build_presence_counts(df, 'programs', 'program')
    assert program_counts.to_dict('records') == [
        {'program': 'PROGRAM A', 'interviews': 2},
        {'program': 'PROGRAM B', 'interviews': 1},
    ]


def test_home_program_total_includes_multi_program_interviews():
    df = pd.DataFrame([
        {'media_id': 'm1', 'author': 'Alice', 'programs': 'Program A, Program B',
         'media_source': 'CNN', 'output': 'TV', 'weight': 1},
        {'media_id': 'm2', 'author': 'Bob', 'programs': 'Program A',
         'media_source': 'BBC', 'output': 'Radio', 'weight': 1},
    ])

    charts, _, _, _ = build_home_dashboard_charts(df, include_engagement_charts=False)

    assert 'Numbers of interviews per programs (Total: 3)' in charts['programs']
    assert 'Numbers of interviews per media output (Total: 2)' in charts['outlets_preview']
    assert 'Number of interviews per media type (Total: 2)' in charts['outputs']


def test_home_author_total_includes_multi_author_interviews():
    df = pd.DataFrame([
        {'media_id': 'm1', 'author': 'Alice, Bob', 'programs': 'Program A',
         'media_source': 'CNN', 'output': 'TV', 'weight': 1},
        {'media_id': 'm2', 'author': 'Alice', 'programs': 'Program B',
         'media_source': 'BBC', 'output': 'Radio', 'weight': 1},
    ])

    charts, _, _, _ = build_home_dashboard_charts(df, include_engagement_charts=False)

    assert 'Total Count: 3' in charts['authors']


def test_build_presence_counts_keeps_rows_without_author_or_media_source():
    df = pd.DataFrame([
        {'media_id': 'm1', 'author': '', 'programs': 'Belief', 'media_source': '', 'output': '', 'weight': 1},
        {'media_id': 'm2', 'author': 'Alice', 'programs': 'Belief', 'media_source': 'CNN', 'output': 'TV', 'weight': 1},
    ])

    author_counts = build_presence_counts(df, 'author', 'author')
    assert author_counts.to_dict('records') == [
        {'author': 'Alice', 'interviews': 1},
        {'author': 'Other/Unknown', 'interviews': 1},
    ]

    media_counts = build_presence_counts(df, 'media_source', 'media')
    assert media_counts.to_dict('records') == [
        {'media': 'CNN', 'interviews': 1},
        {'media': 'OTHER/UNKNOWN', 'interviews': 1},
    ]


def test_build_home_dashboard_charts_omits_engagement_panels_when_requested():
    df = pd.DataFrame([
        {'media_id': 'm1', 'author': 'Alice', 'programs': 'Belief', 'output': 'TV', 'media_source': 'AL JAZEERA', 'weight': 1,
         'facebook_views': 0, 'facebook_total_engagments': 0, 'youtube_views': 0, 'youtube_engagments': 0,
         'twitter_views': 0, 'twitter_total_engagment': 0, 'tiktok_views': 0, 'tiktok_engagments': 0,
         'insta_views': 0, 'instagram_engagment': 0, 'website_views': 0, 'website_engagments': 0, 'web_total_users': 0},
        {'media_id': 'm2', 'author': 'Bob', 'programs': 'Belief', 'output': 'Radio', 'media_source': 'BBC', 'weight': 1,
         'facebook_views': 0, 'facebook_total_engagments': 0, 'youtube_views': 0, 'youtube_engagments': 0,
         'twitter_views': 0, 'twitter_total_engagment': 0, 'tiktok_views': 0, 'tiktok_engagments': 0,
         'insta_views': 0, 'instagram_engagment': 0, 'website_views': 0, 'website_engagments': 0, 'web_total_users': 0},
    ])

    charts, _, _, _ = build_home_dashboard_charts(df, start_date='2024-01-01', end_date='2024-02-01', include_engagement_charts=False)

    assert {'programs', 'outputs', 'outlets_preview', 'outlets_all', 'authors'} <= set(charts)
    assert 'social' not in charts
    assert 'views' not in charts
    assert 'website' not in charts


def test_other_media_dashboard_excludes_home_dashboard_output_types():
    df = pd.DataFrame([
        {'media_id': 'm1', 'author': 'Alice', 'programs': 'Belief', 'output': 'TV', 'media_source': 'AL JAZEERA', 'weight': 1,
         'facebook_views': 0, 'facebook_total_engagments': 0, 'youtube_views': 0, 'youtube_engagments': 0,
         'twitter_views': 0, 'twitter_total_engagment': 0, 'tiktok_views': 0, 'tiktok_engagments': 0,
         'insta_views': 0, 'instagram_engagment': 0, 'website_views': 0, 'website_engagments': 0, 'web_total_users': 0},
        {'media_id': 'm2', 'author': 'Bob', 'programs': 'Belief', 'output': 'Podcast', 'media_source': 'BBC', 'weight': 1,
         'facebook_views': 0, 'facebook_total_engagments': 0, 'youtube_views': 0, 'youtube_engagments': 0,
         'twitter_views': 0, 'twitter_total_engagment': 0, 'tiktok_views': 0, 'tiktok_engagments': 0,
         'insta_views': 0, 'instagram_engagment': 0, 'website_views': 0, 'website_engagments': 0, 'web_total_users': 0},
        {'media_id': 'm3', 'author': 'Carol', 'programs': 'Belief', 'output': 'Radio', 'media_source': 'Spotify', 'weight': 1,
         'facebook_views': 0, 'facebook_total_engagments': 0, 'youtube_views': 0, 'youtube_engagments': 0,
         'twitter_views': 0, 'twitter_total_engagment': 0, 'tiktok_views': 0, 'tiktok_engagments': 0,
         'insta_views': 0, 'instagram_engagment': 0, 'website_views': 0, 'website_engagments': 0, 'web_total_users': 0},
    ])

    charts, _, _, _ = build_home_dashboard_charts(df, start_date='2024-01-01', end_date='2024-02-01',
                                                include_engagement_charts=True, include_excluded_outputs=True)

    assert 'TV' not in charts['outputs']
    assert 'Podcast' not in charts['outputs']
    assert 'Radio' not in charts['outputs']
    assert 'TV' not in charts['programs']
    assert 'TV' not in charts['outlets_all']
    assert 'BBC' not in charts['outlets_all']
    assert {'social', 'views', 'website'} <= set(charts)


def test_preview_outlet_total_matches_visible_bar_sum():
    df = pd.DataFrame([
        {'media_id': 'm1', 'author': 'Alice', 'programs': 'Belief', 'output': 'TV', 'media_source': 'AL JAZEERA', 'weight': 1,
         'facebook_views': 0, 'facebook_total_engagments': 0, 'youtube_views': 0, 'youtube_engagments': 0,
         'twitter_views': 0, 'twitter_total_engagment': 0, 'tiktok_views': 0, 'tiktok_engagments': 0,
         'insta_views': 0, 'instagram_engagment': 0, 'website_views': 0, 'website_engagments': 0, 'web_total_users': 0},
        {'media_id': 'm2', 'author': 'Bob', 'programs': 'Belief', 'output': 'Podcast', 'media_source': 'BBC', 'weight': 1,
         'facebook_views': 0, 'facebook_total_engagments': 0, 'youtube_views': 0, 'youtube_engagments': 0,
         'twitter_views': 0, 'twitter_total_engagment': 0, 'tiktok_views': 0, 'tiktok_engagments': 0,
         'insta_views': 0, 'instagram_engagment': 0, 'website_views': 0, 'website_engagments': 0, 'web_total_users': 0},
        {'media_id': 'm3', 'author': 'Carol', 'programs': 'Belief', 'output': 'Radio', 'media_source': 'CNN', 'weight': 1,
         'facebook_views': 0, 'facebook_total_engagments': 0, 'youtube_views': 0, 'youtube_engagments': 0,
         'twitter_views': 0, 'twitter_total_engagment': 0, 'tiktok_views': 0, 'tiktok_engagments': 0,
         'insta_views': 0, 'instagram_engagment': 0, 'website_views': 0, 'website_engagments': 0, 'web_total_users': 0},
        {'media_id': 'm4', 'author': 'Dan', 'programs': 'Belief', 'output': 'Radio', 'media_source': 'FOX', 'weight': 1,
         'facebook_views': 0, 'facebook_total_engagments': 0, 'youtube_views': 0, 'youtube_engagments': 0,
         'twitter_views': 0, 'twitter_total_engagment': 0, 'tiktok_views': 0, 'tiktok_engagments': 0,
         'insta_views': 0, 'instagram_engagment': 0, 'website_views': 0, 'website_engagments': 0, 'web_total_users': 0},
    ])

    charts, _, _, _ = build_home_dashboard_charts(df, start_date='2024-01-01', end_date='2024-02-01',
                                                include_engagement_charts=False, include_excluded_outputs=True)

    assert '4' in charts['outlets_preview']
    assert '4' in charts['outputs']
    assert 'Total Count' not in charts['outputs']


def test_media_channel_preview_shows_first_15_channels():
    df = pd.DataFrame([
        {'media_id': f'm{i}', 'author': 'Alice', 'programs': 'Belief', 'output': 'TV',
         'media_source': f'CHANNEL {i}', 'weight': 1}
        for i in range(16)
    ])

    charts, _, _, _ = build_home_dashboard_charts(
        df, start_date='2024-01-01', end_date='2024-02-01',
        include_engagement_charts=False
    )

    assert 'Total Count: 16' not in charts['outlets_preview']
    assert 'Numbers of interviews per media output (Total: 16)' in charts['outlets_preview']
    assert 'Numbers of interviews per media output (Total: 16)' in charts['outlets_all']
