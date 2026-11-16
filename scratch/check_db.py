import psycopg2

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')
cur = conn.cursor()

# Get date range of media_output
cur.execute("SELECT MIN(media_date), MAX(media_date), COUNT(*) FROM media_output")
print("Media output date range:", cur.fetchone())

# Get users config
cur.execute("SELECT * FROM users_config")
cols = [desc[0] for desc in cur.description]
print("Users config columns:", cols)
for row in cur.fetchall():
    print(dict(zip(cols, row)))

conn.close()
