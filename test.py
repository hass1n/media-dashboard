import pandas as pd
import sqlite3

def run():
    conn = sqlite3.connect('local_media.db')
    df = pd.read_sql_query('SELECT * FROM unified_media', conn)
    df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(1)
    
    # Programs
    prog_df = df.copy()
    prog_df['programs'] = prog_df['programs'].fillna('Other/Unknown')
    prog_df.loc[prog_df['programs'].str.strip() == '', 'programs'] = 'Other/Unknown'
    prog_df['programs'] = prog_df['programs'].astype(str).str.split(',')
    prog_exploded = prog_df.explode('programs')
    prog_exploded['programs'] = prog_exploded['programs'].str.strip().str.upper()
    prog_exploded = prog_exploded[prog_exploded['programs'] != '']
    prog_exploded = prog_exploded.drop_duplicates(subset=['media_id', 'programs'])
    prog_sum = prog_exploded['weight'].sum()
    
    # Outlets
    outlets_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].drop_duplicates(subset=['media_id', 'media_source']).copy()
    outlets_df = outlets_df[outlets_df['media_source'].notna() & (outlets_df['media_source'].str.strip() != '')]
    outlets_sum = outlets_df['weight'].sum()
    
    # Outputs
    out_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
    out_df['output'] = out_df['output'].fillna('Other/Unknown')
    out_df.loc[out_df['output'].str.strip() == '', 'output'] = 'Other/Unknown'
    out_df['output'] = out_df['output'].astype(str).str.split(',')
    out_exploded = out_df.explode('output')
    out_exploded['output'] = out_exploded['output'].str.strip()
    out_exploded = out_exploded[out_exploded['output'] != '']
    out_exploded = out_exploded.drop_duplicates(subset=['media_id', 'output'])
    
    exclude_list = ['economic update', 'research', 'conference', 'economic news']
    out_exploded_filtered = out_exploded[~out_exploded['output'].str.lower().isin(exclude_list)]
    out_sum = out_exploded_filtered['weight'].sum()
    
    out_counts = out_exploded['output'].value_counts()
    
    print(f"Prog sum: {prog_sum}")
    print(f"Outlets sum: {outlets_sum}")
    print(f"Outputs (raw count): {len(out_exploded)}")
    print(f"Outputs filtered (raw count): {len(out_exploded_filtered)}")
    print(f"Outputs filtered sum (weight): {out_sum}")
    
run()
