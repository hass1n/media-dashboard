import pandas as pd
import sqlite3

conn = sqlite3.connect('local_media.db')
df = pd.read_sql_query('SELECT programs, output, media_source, author FROM unified_media', conn)

for col in ['programs', 'output', 'author']:
    mults = df[col].astype(str).str.contains(',').sum()
    print(f"Interviews with multiple {col}: {mults}")
