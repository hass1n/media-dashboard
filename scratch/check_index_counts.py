import sys
sys.path.append('.')
import psycopg2
import pandas as pd

from app import get_unified_media_df

start_date = '2020-02-01'
end_date = '2026-06-01'

df = get_unified_media_df(start_date, end_date)
print(f"Total rows retrieved from get_unified_media_df between {start_date} and {end_date}: {len(df)}")

# Standardize media names
from app import standardize_media_name
df['media_source'] = df['media_source'].apply(standardize_media_name)

# Filter for interviews, etc.
is_interview = df['output'].str.contains('interview', case=False, na=False)
is_oped = df['output'].str.contains('op-ed', case=False, na=False)
is_news_website = df['output'].str.contains('news website', case=False, na=False)
is_economic = df['output'].str.contains('economic', case=False, na=False)
interview_df = df[is_interview | is_oped | is_news_website | is_economic].copy()
print(f"Total rows after interview filter: {len(interview_df)}")

# Program counts logic
prog_df = interview_df[~interview_df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
prog_df = prog_df[prog_df['programs'].notna()]
print(f"Total rows with programs (main only): {len(prog_df)}")
if not prog_df.empty:
    prog_df['programs'] = prog_df['programs'].astype(str).str.split(',')
    prog_exploded = prog_df.explode('programs')
    prog_exploded['programs'] = prog_exploded['programs'].str.strip().str.upper()
    prog_exploded = prog_exploded[prog_exploded['programs'] != '']
    from app import MEDIA_KEYWORDS
    prog_exploded = prog_exploded[~prog_exploded['programs'].isin(MEDIA_KEYWORDS)]
    prog_exploded = prog_exploded.drop_duplicates(subset=['media_id', 'programs'])
    print(f"Total exploded & deduplicated program-rows: {len(prog_exploded)}")
    prog_counts = prog_exploded.groupby('programs')['media_id'].count().reset_index()
    prog_counts.columns = ['program', 'interviews']
    prog_counts = prog_counts.sort_values(by='interviews', ascending=False)
    print("Program counts before 'OTHER' filtering:")
    print(prog_counts)
    
    # Filter 'OTHER'
    other_mask = prog_counts['program'] == 'OTHER'
    if other_mask.any():
        other_index = prog_counts[other_mask].index[0]
        prog_counts_filtered = prog_counts.loc[:other_index].reset_index(drop=True)
        print("Program counts after 'OTHER' filtering:")
        print(prog_counts_filtered)

# Author counts logic
auth_df = interview_df[~interview_df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
auth_df = auth_df[auth_df['author'].notna() & (auth_df['author'].str.strip() != '')]
print(f"Total rows with authors (main only): {len(auth_df)}")
if not auth_df.empty:
    auth_df['author'] = auth_df['author'].astype(str).str.split(',')
    auth_exploded = auth_df.explode('author')
    auth_exploded['author'] = auth_exploded['author'].str.strip()
    auth_exploded = auth_exploded[auth_exploded['author'] != '']
    auth_exploded = auth_exploded.drop_duplicates(subset=['media_id', 'author'])
    auth_counts = auth_exploded.groupby('author')['media_id'].count().reset_index()
    auth_counts.columns = ['author', 'interviews']
    auth_counts = auth_counts.sort_values(by='interviews', ascending=False)
    print("Author counts:")
    print(auth_counts.head(20))
