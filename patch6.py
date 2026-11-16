import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Media Output (Chart 2)
outlets_old = '''    outlets_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].drop_duplicates(subset=['media_id', 'media_source']).copy()
    outlets_df = outlets_df[outlets_df['media_source'].notna() & (outlets_df['media_source'].str.strip() != '')]'''

outlets_new = '''    outlets_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    outlets_df['media_source'] = outlets_df['media_source'].fillna('Other/Unknown')
    outlets_df.loc[outlets_df['media_source'].str.strip() == '', 'media_source'] = 'Other/Unknown'
    outlets_df = outlets_df.drop_duplicates(subset=['media_id'])'''

content = content.replace(outlets_old, outlets_new)

# 2. Update Output Type (Chart 3)
outputs_old = '''    out_df['output'] = out_df['output'].astype(str).str.split(',')
    out_exploded = out_df.explode('output')
    out_exploded['output'] = out_exploded['output'].str.strip()
    out_exploded = out_exploded[out_exploded['output'] != '']
    out_exploded = out_exploded.drop_duplicates(subset=['media_id', 'output'])
    
    exclude_list = ['economic update', 'research', 'conference', 'economic updates', 'economic news']
    out_exploded = out_exploded[~out_exploded['output'].str.lower().isin(exclude_list)]'''

outputs_new = '''    out_df['output'] = out_df['output'].astype(str).apply(lambda x: x.split(',')[0].strip() if x.strip() else 'Other/Unknown')
    out_exploded = out_df.drop_duplicates(subset=['media_id'])'''

content = content.replace(outputs_old, outputs_new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
