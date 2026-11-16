import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

query = "SELECT SUM(COALESCE(media_whatsapp, 0)) FROM media_output WHERE media_date >= '2025-05-13'"
result = pd.read_sql(query, engine)
print(f"Total WhatsApp Sent: {result.iloc[0,0]}")
