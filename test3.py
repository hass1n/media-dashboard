import pandas as pd
import sqlite3

conn = sqlite3.connect('local_media.db')
df = pd.read_sql_query('SELECT * FROM unified_media', conn)
print("Total unique media_id:", df['media_id'].nunique())
interviews = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))]
print("Total non-p/sm media_id:", interviews['media_id'].nunique())
