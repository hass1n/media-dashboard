import psycopg2
import pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')

# Count main rows
main_sql = """
SELECT COUNT(*) as main_rows
FROM media_output 
WHERE media_date BETWEEN '2026-01-01' AND '2026-01-31'
"""
main_count = pd.read_sql_query(main_sql, conn)

# Count parts rows
parts_sql = """
SELECT COUNT(*) as part_rows
FROM media_parts mp
JOIN media_output mo ON mp.media_id = mo.media_id
WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
"""
parts_count = pd.read_sql_query(parts_sql, conn)

print("Row Count Breakdown for January 2026:")
print("-" * 50)
print(f"Main media_output rows: {int(main_count['main_rows'].iloc[0])}")
print(f"Parts (TV/Radio interview segments): {int(parts_count['part_rows'].iloc[0])}")
print(f"Total rows in dashboard: {int(main_count['main_rows'].iloc[0] + parts_count['part_rows'].iloc[0])}")
print()

# Now check website metrics for MAIN rows only
main_web = """
SELECT 
    SUM(mk.website_views) as total_web_views,
    SUM(mk.website_event_count) as total_web_eng
FROM media_output mo
LEFT JOIN media_kpis mk ON mo.media_id = mk.media_id
WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
"""
main_web_result = pd.read_sql_query(main_web, conn)

print("Website Metrics (MAIN rows only):")
print("-" * 50)
mwv = int(main_web_result['total_web_views'].iloc[0] or 0)
mwe = int(main_web_result['total_web_eng'].iloc[0] or 0)
print(f"Website Views (main): {mwv:,}")
print(f"Website Engagements (main): {mwe:,}")
print()

# Now check website metrics for PARTS only
parts_web = """
SELECT 
    SUM(pk.part_website_views) as total_part_web_views,
    SUM(pk.part_website_event_count) as total_part_web_eng
FROM media_parts mp
JOIN media_output mo ON mp.media_id = mo.media_id
LEFT JOIN parts_kpis pk ON mp.part_id = pk.part_id
WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
"""
parts_web_result = pd.read_sql_query(parts_web, conn)

pwv = int(parts_web_result['total_part_web_views'].iloc[0] or 0)
pwe = int(parts_web_result['total_part_web_eng'].iloc[0] or 0)
print("Website Metrics (PARTS only):")
print("-" * 50)
print(f"Website Views (parts): {pwv:,}")
print(f"Website Engagements (parts): {pwe:,}")
print()

print("TOTALS (Main + Parts):")
print("-" * 50)
print(f"Website Views: {mwv + pwv:,}")
print(f"Website Engagements: {mwe + pwe:,}")
print()

print("YOUR EXPORTED TOTALS:")
print("-" * 50)
print(f"Website Views: 9,150")
print(f"Website Engagements: 24,550")
print()

if (mwv + pwv) == 9150 and (mwe + pwe) == 24550:
    print("✅ DATABASE MATCHES YOUR EXPORT")
elif mwv == 9150 and mwe == 24550:
    print("⚠️  MAIN ROWS MATCH - Parts are NOT in your export")
else:
    print(f"❌ MISMATCH: DB has {mwv + pwv:,} views, {mwe + pwe:,} engagements")
    print(f"   Your export has 9,150 views, 24,550 engagements")
    print(f"   Difference: {(mwv + pwv) - 9150:,} views, {(mwe + pwe) - 24550:,} engagements")

conn.close()
