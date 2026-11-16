import pandas as pd
import sqlite3

def run():
    conn = sqlite3.connect('local_media.db')
    df = pd.read_sql_query('SELECT * FROM unified_media', conn)
    df['weight'] = 1
    
    # Global filter
    exclude_list = ['economic update', 'research', 'conference', 'economic updates', 'economic news']
    def should_exclude(val):
        if pd.isna(val): return False
        parts = [p.strip().lower() for p in str(val).split(',')]
        return any(p in exclude_list for p in parts)
    df = df[~df['output'].apply(should_exclude)]
    
    # 1. Programs sum
    prog_df = df.copy()
    prog_df['programs'] = prog_df['programs'].fillna('Other/Unknown')
    prog_df.loc[prog_df['programs'].str.strip() == '', 'programs'] = 'Other/Unknown'
    prog_df['programs'] = prog_df['programs'].astype(str).str.split(',')
    prog_exploded = prog_df.explode('programs')
    prog_exploded['programs'] = prog_exploded['programs'].str.strip().str.upper()
    prog_exploded = prog_exploded[prog_exploded['programs'] != '']
    prog_exploded = prog_exploded.drop_duplicates(subset=['media_id', 'programs'])
    prog_counts = prog_exploded.groupby('programs')['weight'].sum()
    prog_sum = prog_counts.sum()
    
    # 2. Media Output
    outlets_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].drop_duplicates(subset=['media_id', 'media_source']).copy()
    outlets_df = outlets_df[outlets_df['media_source'].notna() & (outlets_df['media_source'].str.strip() != '')]
    outlet_counts = outlets_df.groupby('media_source')['weight'].sum()
    outlet_sum = outlet_counts.sum()
    
    # 3. Output Type
    out_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    out_df['output'] = out_df['output'].fillna('Other/Unknown')
    out_df.loc[out_df['output'].str.strip() == '', 'output'] = 'Other/Unknown'
    out_df['output'] = out_df['output'].astype(str).str.split(',')
    out_exploded = out_df.explode('output')
    out_exploded['output'] = out_exploded['output'].str.strip()
    out_exploded = out_exploded[out_exploded['output'] != '']
    out_exploded = out_exploded.drop_duplicates(subset=['media_id', 'output'])
    out_counts = out_exploded['output'].value_counts()
    out_sum = out_counts.sum()
    
    # 4. Authors
    auth_df = df.copy()
    auth_df['author'] = auth_df['author'].fillna('Other/Unknown')
    auth_df.loc[auth_df['author'].str.strip() == '', 'author'] = 'Other/Unknown'
    auth_df['author'] = auth_df['author'].astype(str).str.split(',')
    auth_exploded = auth_df.explode('author')
    auth_exploded['author'] = auth_exploded['author'].str.strip().str.upper()
    auth_exploded = auth_exploded[auth_exploded['author'] != '']
    auth_exploded = auth_exploded.drop_duplicates(subset=['media_id', 'author'])
    auth_counts = auth_exploded.groupby('author')['weight'].sum()
    auth_sum = auth_counts.sum()
    
    print(f"Prog sum: {prog_sum}")
    print(f"Outlet sum: {outlet_sum}")
    print(f"Output type sum: {out_sum}")
    print(f"Author sum: {auth_sum}")
    
run()
