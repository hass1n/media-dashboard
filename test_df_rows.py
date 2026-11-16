import pandas as pd
from app import get_unified_media_df

start_date = '2020-02-01'
end_date = '2026-06-01'

df = get_unified_media_df(start_date, end_date)
print(f"Total rows in df: {len(df)}")
print(f"Unique media_ids in df: {df['media_id'].nunique()}")
