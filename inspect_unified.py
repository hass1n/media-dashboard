import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('local_media.db')
cur = conn.cursor()

print('PRAGMA table_info(unified_media):')
cur.execute("PRAGMA table_info('unified_media')")
cols = cur.fetchall()
for c in cols:
    print(c)

print('\nSample column names:')
col_names = [c[1] for c in cols]
print(col_names)

print('\nCount rows for January 2026:')
try:
    cur.execute("SELECT COUNT(*) FROM unified_media WHERE media_date BETWEEN '2026-01-01' AND '2026-01-31'")
    print(cur.fetchone()[0])
except Exception as e:
    print('Count query failed:', e)

print('\nSample 5 rows:')
cur.execute("SELECT * FROM unified_media WHERE media_date BETWEEN '2026-01-01' AND '2026-01-31' LIMIT 5")
rows = cur.fetchall()
for r in rows:
    print(r)

conn.close()
