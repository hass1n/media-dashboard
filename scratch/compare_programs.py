import psycopg2
import pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

# Find if any parts have different programs than their parent media
query = """
SELECT mp.media_id, mp.part_id, 
       (SELECT string_agg(media_program, ', ') FROM media_programs WHERE media_id = mp.media_id) as parent_programs,
       (SELECT string_agg(part_program_name, ', ') FROM parts_programs WHERE part_id = mp.part_id) as part_programs
FROM media_parts mp
ORDER BY mp.media_id
"""
df = pd.read_sql(query, conn)
different = df[df['parent_programs'] != df['part_programs']]
print("Number of parts with different programs than parent:", len(different))
if len(different) > 0:
    print(different.head(20))

conn.close()
