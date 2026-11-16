import psycopg2
import pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

# Let's count media types
query_types = """
SELECT media_type, COUNT(DISTINCT media_id) 
FROM media_types 
GROUP BY media_type 
ORDER BY count DESC
"""
print("--- Media Types counts ---")
df_t = pd.read_sql(query_types, conn)
print(df_t)

conn.close()
