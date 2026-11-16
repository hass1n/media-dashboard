import psycopg2
import pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

# Let's count interviews per program in the DB
# (main media rows only? or all?)
# Let's see what is the total count in media_programs for all programs
query_programs = """
SELECT media_program, COUNT(DISTINCT media_id) 
FROM media_programs 
GROUP BY media_program 
ORDER BY count DESC
"""
print("--- Programs counts from media_programs table ---")
df_p = pd.read_sql(query_programs, conn)
print(df_p)

# Let's count authors from media_authors table
query_authors = """
SELECT author_name, COUNT(DISTINCT media_id) 
FROM media_authors 
GROUP BY author_name 
ORDER BY count DESC
"""
print("\n--- Authors counts from media_authors table ---")
df_a = pd.read_sql(query_authors, conn)
print(df_a)

conn.close()
