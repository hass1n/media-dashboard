import sys
sys.path.append('.')
import pandas as pd
from app import get_unified_media_df, standardize_media_name, MEDIA_KEYWORDS

df = get_unified_media_df('2020-02-01', '2026-06-01')
df['media_source'] = df['media_source'].apply(standardize_media_name)

# Program counts logic (unfiltered)
prog_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
prog_df = prog_df[prog_df['programs'].notna()]
prog_df['programs'] = prog_df['programs'].astype(str).str.split(',')
prog_exploded = prog_df.explode('programs')
prog_exploded['programs'] = prog_exploded['programs'].str.strip().str.upper()
prog_exploded = prog_exploded[prog_exploded['programs'] != '']
prog_exploded = prog_exploded[~prog_exploded['programs'].isin(MEDIA_KEYWORDS)]
prog_exploded = prog_exploded.drop_duplicates(subset=['media_id', 'programs'])

prog_counts = prog_exploded.groupby('programs')['media_id'].count().reset_index()
prog_counts.columns = ['program', 'interviews']
prog_counts = prog_counts.sort_values(by='interviews', ascending=False)
print("Unfiltered Program Counts:")
print(prog_counts)

# Author counts logic (unfiltered)
auth_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
auth_df = auth_df[auth_df['author'].notna() & (auth_df['author'].str.strip() != '')]
auth_df['author'] = auth_df['author'].astype(str).str.split(',')
auth_exploded = auth_df.explode('author')
auth_exploded['author'] = auth_exploded['author'].str.strip()
auth_exploded = auth_exploded[auth_exploded['author'] != '']
auth_exploded = auth_exploded.drop_duplicates(subset=['media_id', 'author'])

auth_counts = auth_exploded.groupby('author')['media_id'].count().reset_index()
auth_counts.columns = ['author', 'interviews']
auth_counts = auth_counts.sort_values(by='interviews', ascending=False)
print("\nUnfiltered Author Counts:")
print(auth_counts.head(20))
