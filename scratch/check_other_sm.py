import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')

df = pd.read_sql("SELECT * FROM sm_parts WHERE sm_platform = 'Other platform'", engine)
print(df[['sm_title', 'sm_views', 'sm_likes']])
