import app

def calc_author_media_totals(df):
    df = df.copy()
    df['media_source'] = df['media_source'].apply(app.standardize_media_name)
    df['weight'] = 1
    valid = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()

    auth = valid[valid['author'].notna() & (valid['author'].astype(str).str.strip() != '')].copy()
    auth = auth.drop_duplicates(subset=['media_id']).copy()
    auth['author'] = auth['author'].astype(str).str.split(',')
    auth = auth.explode('author')
    auth['author'] = auth['author'].str.strip()
    auth = auth[auth['author'] != '']
    auth = auth.drop_duplicates(subset=['media_id', 'author'])
    auth_total = auth.groupby('author')['weight'].sum().sum()

    media = valid[valid['media_source'].notna() & (valid['media_source'].astype(str).str.strip() != '')].copy()
    media = media.drop_duplicates(subset=['media_id']).copy()
    media['media_source'] = media['media_source'].astype(str).str.split(',')
    media = media.explode('media_source')
    media['media_source'] = media['media_source'].str.strip()
    media = media[media['media_source'] != '']
    media = media.drop_duplicates(subset=['media_id', 'media_source'])
    media_total = media.groupby('media_source')['weight'].sum().sum()

    return auth_total, media_total

full = app.get_unified_media_df('2020-02-01', '2026-06-01')
print('FULL totals:', calc_author_media_totals(full))

programs = ['POLITICS', 'HEALTH']
for name in programs:
    df = full[full['programs'].astype(str).str.contains(name, case=False, na=False)]
    print(f'{name} totals:', calc_author_media_totals(df))

categories = ['POLITICS', 'ECONOMY']
for name in categories:
    df = full[full['categories'].astype(str).str.contains(name, case=False, na=False)]
    print(f'CATEGORY {name} totals:', calc_author_media_totals(df))
