import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

query = """
SELECT SUM(COALESCE(youtube_views, 0) + COALESCE(source_youtube_views, 0))
FROM media_kpis
WHERE media_id NOT IN (
    SELECT media_id FROM media_output WHERE media_date >= '2025-05-13'
)
"""

result = pd.read_sql(query, engine)
print(f"Views in media_kpis NOT in media_output for last year: {result.iloc[0,0]}")
