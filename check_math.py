import pandas as pd
import sqlite3
import numpy as np

conn = sqlite3.connect('local_media.db')
df = pd.read_sql_query('SELECT * FROM unified_media', conn)
df['weight'] = 1

exclude_list = ['economic update', 'research', 'conference', 'economic updates', 'economic news']
def should_exclude(val):
    if pd.isna(val): return False
    parts = [p.strip().lower() for p in str(val).split(',')]
    return any(p in exclude_list for p in parts)

df = df[~df['output'].apply(should_exclude)]

# Unique non-p/sm
base_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))]
print("Total unique interviews after global filter:", base_df['media_id'].nunique())

# Media Channel (outlets_df)
outlets_df = base_df.drop_duplicates(subset=['media_id', 'media_source']).copy()
empty_source = outlets_df['media_source'].isna() | (outlets_df['media_source'].str.strip() == '')
print(f"Missing media_source: {empty_source.sum()}")
outlets_df = outlets_df[~empty_source]
print("Media Channel sum:", outlets_df['weight'].sum())

# Media Type (Output Type)
out_df = base_df.copy()
out_df['output'] = out_df['output'].fillna('Other/Unknown')
out_df.loc[out_df['output'].str.strip() == '', 'output'] = 'Other/Unknown'
out_df['output'] = out_df['output'].astype(str).str.split(',')
out_exploded = out_df.explode('output')
out_exploded['output'] = out_exploded['output'].str.strip()
out_exploded = out_exploded[out_exploded['output'] != '']
out_exploded = out_exploded.drop_duplicates(subset=['media_id', 'output'])
print("Media Type sum:", out_exploded['weight'].sum())

# Let's see if there are multiple outputs per media_id in out_exploded
mult_outputs = out_exploded.groupby('media_id').size()
print("Media with >1 output:", (mult_outputs > 1).sum())

# Authors
auth_df = base_df.copy()
auth_df['author'] = auth_df['author'].fillna('Other/Unknown')
auth_df.loc[auth_df['author'].str.strip() == '', 'author'] = 'Other/Unknown'
auth_df['author'] = auth_df['author'].astype(str).str.split(',')
auth_exploded = auth_df.explode('author')
auth_exploded['author'] = auth_exploded['author'].str.strip().str.upper()
auth_exploded = auth_exploded[auth_exploded['author'] != '']
auth_exploded = auth_exploded.drop_duplicates(subset=['media_id', 'author'])
print("Author sum:", auth_exploded['weight'].sum())

