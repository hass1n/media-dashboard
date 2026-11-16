import pandas as pd
import sqlite3

conn = sqlite3.connect('local_media.db')
df = pd.read_sql_query('SELECT * FROM unified_media', conn)
df['weight'] = 1

exclude_list = ['economic update', 'research', 'conference', 'economic updates', 'economic news']
def should_exclude(val):
    if pd.isna(val): return False
    parts = [p.strip().lower() for p in str(val).split(',')]
    return any(p in exclude_list for p in parts)

df = df[~df['output'].apply(should_exclude)]

base_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()

# 1. Media Channel (outlets_df)
outlets_df = base_df.copy()
outlets_df['media_source'] = outlets_df['media_source'].fillna('Other/Unknown')
outlets_df.loc[outlets_df['media_source'].str.strip() == '', 'media_source'] = 'Other/Unknown'
outlets_df = outlets_df.drop_duplicates(subset=['media_id'])
print("Media Channel sum:", outlets_df['weight'].sum())

# 2. Media Type (out_df)
out_df = base_df.copy()
out_df['output'] = out_df['output'].fillna('Other/Unknown')
out_df.loc[out_df['output'].str.strip() == '', 'output'] = 'Other/Unknown'
out_df['output'] = out_df['output'].astype(str).apply(lambda x: x.split(',')[0].strip() if x.strip() else 'Other/Unknown')
out_df = out_df.drop_duplicates(subset=['media_id'])
out_counts = out_df['output'].value_counts()
print("Media Type sum:", out_counts.sum())

