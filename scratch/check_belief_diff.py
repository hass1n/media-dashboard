import psycopg2
import pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

# Let's check the date range we retrieved in Python: 2020-02-01 to 2026-06-01
start_date = '2020-02-01'
end_date = '2026-06-01'

# 1. Parents count in DB for BELIEF
query_parent_belief = """
SELECT COUNT(DISTINCT mo.media_id)
FROM media_output mo
JOIN media_programs mp ON mo.media_id = mp.media_id
WHERE mo.media_date BETWEEN %s AND %s
  AND mp.media_program = 'BELIEF'
"""
cur = conn.cursor()
cur.execute(query_parent_belief, (start_date, end_date))
print("Parent rows count for BELIEF in DB:", cur.fetchone()[0])

# 2. Let's see how many parts have BELIEF program
query_parts_belief = """
SELECT COUNT(*) 
FROM media_parts mp
JOIN parts_programs pp ON mp.part_id = pp.part_id
JOIN media_output mo ON mp.media_id = mo.media_id
WHERE mo.media_date BETWEEN %s AND %s
  AND pp.part_program_name = 'BELIEF'
"""
cur.execute(query_parts_belief, (start_date, end_date))
print("Parts rows count for BELIEF in DB:", cur.fetchone()[0])

# 3. Python chart logic count for BELIEF (from app.py)
# Which is:
#  - get_unified_media_df
#  - filter for output types: is_interview | is_oped | is_news_website | is_economic
#  - count main rows only
# Let's count how many main rows with BELIEF program pass this filter
query_python_logic = """
SELECT COUNT(DISTINCT mo.media_id)
FROM media_output mo
JOIN media_programs mp ON mo.media_id = mp.media_id
LEFT JOIN media_types mt ON mo.media_id = mt.media_id
WHERE mo.media_date BETWEEN %s AND %s
  AND mp.media_program = 'BELIEF'
  AND (
    LOWER(mt.media_type) LIKE '%%interview%%'
    OR LOWER(mt.media_type) LIKE '%%op-ed%%'
    OR LOWER(mt.media_type) LIKE '%%news website%%'
    OR LOWER(mt.media_type) LIKE '%%economic%%'
  )
"""
cur.execute(query_python_logic, (start_date, end_date))
print("Python chart logic count for BELIEF (main rows, filtered by output type):", cur.fetchone()[0])

conn.close()
