import psycopg2
import sys

# Set output encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')
cur = conn.cursor()

sql = '''
SELECT 
    mo.media_id,
    mo.title,
    mk.website_views,
    mk.website_event_count
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
ORDER BY mo.media_date DESC, mo.media_id DESC
LIMIT 15
'''

cur.execute(sql)
rows = cur.fetchall()

print("First 15 rows - Website Views and Engagements:")
print()
total_views = 0
total_eng = 0
for idx, row in enumerate(rows, 1):
    media_id = row[0]
    title = str(row[1])[:40] if row[1] else "NO TITLE"
    views = row[2] if row[2] else 0
    engagements = row[3] if row[3] else 0
    total_views += views
    total_eng += engagements
    print(f"Row {idx}: Views={views} | Engagements={engagements}")

print()
print(f"Sum of first 15 rows: Views={total_views} | Engagements={total_eng}")
print()
print("Your first 5 values: 10, 44, 11, 9, 16 (total = 90)")

conn.close()
