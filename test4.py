import pandas as pd
import sqlite3

conn = sqlite3.connect('local_media.db')
df = pd.read_sql_query('SELECT output FROM unified_media', conn)

print("Total rows:", len(df))
exclude = ['economic update', 'research', 'conference', 'economic news', 'economic updates']

def has_exclude(val):
    if pd.isna(val): return False
    parts = [p.strip().lower() for p in str(val).split(',')]
    return any(p in exclude for p in parts)

df['has_ex'] = df['output'].apply(has_exclude)

def is_only_exclude(val):
    if pd.isna(val): return False
    parts = [p.strip().lower() for p in str(val).split(',')]
    # Return true if ALL parts are in exclude
    return all(p in exclude or p == '' for p in parts)

df['only_ex'] = df['output'].apply(is_only_exclude)

print("Rows with exclude:", df['has_ex'].sum())
print("Rows that are ONLY exclude:", df['only_ex'].sum())
