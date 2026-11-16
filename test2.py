import pandas as pd
import sqlite3

conn = sqlite3.connect('local_media.db')
df = pd.read_sql_query('SELECT * FROM unified_media LIMIT 1', conn)
print(df.columns.tolist())
