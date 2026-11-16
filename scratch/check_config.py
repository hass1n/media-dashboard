import warnings; warnings.filterwarnings('ignore')
import psycopg2, json, pandas as pd

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')
cur = conn.cursor()

# Check tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)
print()

# Check users_config
if 'users_config' in tables:
    uc = pd.read_sql_query("SELECT * FROM users_config", conn)
    print("users_config columns:", list(uc.columns))
    for _, row in uc.iterrows():
        print("\n--- User config row ---")
        for col in uc.columns:
            print(f"  {col}: {row[col]}")
else:
    print("No users_config table - checking users table instead")
    if 'users' in tables:
        u = pd.read_sql_query("SELECT * FROM users", conn)
        print("users:", u.to_string())

# Also check what types exist in media_types for Jan 2026
print("\n--- Media types in Jan 2026 ---")
mt = pd.read_sql_query("""
    SELECT mt.media_type, COUNT(*) as cnt
    FROM media_output mo
    JOIN media_types mt ON mo.media_id = mt.media_id
    WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
    GROUP BY mt.media_type ORDER BY cnt DESC
""", conn)
print(mt.to_string())

# Check programs in Jan 2026
print("\n--- Programs in Jan 2026 ---")
mp = pd.read_sql_query("""
    SELECT mp.media_program, COUNT(*) as cnt
    FROM media_output mo
    JOIN media_programs mp ON mo.media_id = mp.media_id
    WHERE mo.media_date BETWEEN '2026-01-01' AND '2026-01-31'
    GROUP BY mp.media_program ORDER BY cnt DESC
""", conn)
print(mp.to_string())

conn.close()
