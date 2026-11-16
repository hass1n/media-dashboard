import psycopg2
import pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

# Get ONLY website metrics for January 2026 (main media_output only)
sql = '''
SELECT 
    COUNT(DISTINCT mo.media_id) as media_count,
    SUM(mk.website_views) as total_website_views,
    SUM(mk.website_event_count) as total_website_engagements
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
'''

result = pd.read_sql_query(sql, conn)
print('MAIN media_output rows only:')
print(result)
print()

# Now add parts
sql2 = '''
SELECT 
    COUNT(DISTINCT mp.part_id) as part_count,
    SUM(pk.part_website_views) as part_website_views,
    SUM(pk.part_website_event_count) as part_website_engagements
FROM media_parts mp
JOIN media_output mo ON mp.media_id = mo.media_id
LEFT JOIN parts_kpis pk ON mp.part_id = pk.part_id
WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
'''

result2 = pd.read_sql_query(sql2, conn)
print('PARTS (TV/Radio interviews) rows:')
print(result2)
print()

print('--- WEBSITE METRICS TOTALS ---')
mw = float(result['total_website_views'].iloc[0] or 0)
me = float(result['total_website_engagements'].iloc[0] or 0)
pw = float(result2['part_website_views'].iloc[0]) if pd.notna(result2['part_website_views'].iloc[0]) else 0
pe = float(result2['part_website_engagements'].iloc[0]) if pd.notna(result2['part_website_engagements'].iloc[0]) else 0
print(f'Main Website Views: {int(mw):,}')
print(f'Main Website Engagements: {int(me):,}')
print(f'Parts Website Views: {int(pw):,}')
print(f'Parts Website Engagements: {int(pe):,}')
print(f'\nTOTAL Website Views: {int(mw+pw):,}')
print(f'TOTAL Website Engagements: {int(me+pe):,}')

conn.close()
