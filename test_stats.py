import pandas as pd
from app import get_unified_media_df

start_date = '2020-02-01'
end_date = '2026-06-01'

df = get_unified_media_df(start_date, end_date)

platforms = ['facebook', 'youtube', 'twitter', 'tiktok', 'instagram', 'website']
print("From get_unified_media_df:")
for p in platforms:
    views_col = [c for c in df.columns if p in c and 'view' in c]
    eng_col = [c for c in df.columns if p in c and 'engag' in c]
    print(f"{p}: views cols: {views_col}, eng cols: {eng_col}")
    if views_col:
        print(f"  views sum: {df[views_col[0]].sum()}")
    if eng_col:
        print(f"  eng sum: {df[eng_col[-1]].sum()}")
