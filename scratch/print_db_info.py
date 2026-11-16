import psycopg2

conn = psycopg2.connect(host='localhost', dbname='media_db_4', user='postgres', password='1234')
cur = conn.cursor()

# Get date range of media_output
cur.execute("SELECT MIN(media_date), MAX(media_date), COUNT(*) FROM media_output")
print("Media output date range in DB:", cur.fetchone())

# Find out what the user configs have for start_date and end_date
cur.execute("SELECT user_id, start_date, end_date FROM users_config")
for row in cur.fetchall():
    print(f"User {row[0]}: start={row[1]}, end={row[2]}")

conn.close()
