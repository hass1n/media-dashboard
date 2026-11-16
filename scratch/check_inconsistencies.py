import sys
sys.path.append('.')
import pandas as pd
from app import get_unified_media_df, standardize_media_name

df = get_unified_media_df('2020-02-01', '2026-06-01')
df['media_source'] = df['media_source'].apply(standardize_media_name)

# Home page filtered subsets
is_interview = df['output'].str.contains('interview', case=False, na=False)
is_oped = df['output'].str.contains('op-ed', case=False, na=False)
is_news_website = df['output'].str.contains('news website', case=False, na=False)
is_economic = df['output'].str.contains('economic', case=False, na=False)
interview_df = df[is_interview | is_oped | is_news_website | is_economic].copy()

# GARO counts
print("=== GARO ===")
# 1. Home page authors chart count for Garo
auth_df_home = interview_df[~interview_df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
auth_df_home = auth_df_home[auth_df_home['author'].notna() & (auth_df_home['author'].str.strip() != '')]
auth_df_home['author'] = auth_df_home['author'].astype(str).str.split(',')
auth_exploded_home = auth_df_home.explode('author')
auth_exploded_home['author'] = auth_exploded_home['author'].str.strip()
auth_exploded_home = auth_exploded_home.drop_duplicates(subset=['media_id', 'author'])
garo_home = auth_exploded_home[auth_exploded_home['author'].str.lower() == 'garo']
print("Garo count on Home page authors chart:", len(garo_home))

# 2. Author page programs chart count for Garo
df_garo = df[df['author'].astype(str).str.contains('Garo', case=False, na=False)].copy()
df_expl = df_garo.copy()
df_expl['programs'] = df_expl['programs'].astype(str).str.split(',')
df_expl = df_expl.explode('programs')
df_expl['programs'] = df_expl['programs'].str.strip().str.upper()
df_expl = df_expl[df_expl['programs'] != '']
from app import MEDIA_KEYWORDS
df_expl = df_expl[~df_expl['programs'].isin(MEDIA_KEYWORDS)]
df_expl = df_expl.drop_duplicates(subset=['media_id', 'programs'])
print("Garo programs chart total interviews (sum on Garo detail page):", df_expl.groupby('programs')['media_id'].count().sum())

# BELIEF counts
print("\n=== BELIEF ===")
# 1. Home page programs chart count for Belief
prog_df_home = interview_df[~interview_df['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
prog_df_home = prog_df_home[prog_df_home['programs'].notna()]
prog_df_home['programs'] = prog_df_home['programs'].astype(str).str.split(',')
prog_exploded_home = prog_df_home.explode('programs')
prog_exploded_home['programs'] = prog_exploded_home['programs'].str.strip().str.upper()
prog_exploded_home = prog_exploded_home[prog_exploded_home['programs'] != '']
prog_exploded_home = prog_exploded_home[~prog_exploded_home['programs'].isin(MEDIA_KEYWORDS)]
prog_exploded_home = prog_exploded_home.drop_duplicates(subset=['media_id', 'programs'])
belief_home = prog_exploded_home[prog_exploded_home['programs'] == 'BELIEF']
print("Belief count on Home page programs chart:", len(belief_home))

# 2. Program page authors chart count for Belief
df_belief = df[df['programs'].str.contains('BELIEF', case=False, na=False)].copy()
auth_df_belief = df_belief[~df_belief['media_id'].astype(str).str.startswith(('p', 'sm'))].copy()
auth_df_belief = auth_df_belief[auth_df_belief['author'].notna() & (auth_df_belief['author'].str.strip() != '')]
auth_df_belief['author'] = auth_df_belief['author'].astype(str).str.split(',')
auth_exploded_belief = auth_df_belief.explode('author')
auth_exploded_belief['author'] = auth_exploded_belief['author'].str.strip()
auth_exploded_belief = auth_exploded_belief[auth_exploded_belief['author'] != '']
auth_exploded_belief = auth_exploded_belief.drop_duplicates(subset=['media_id', 'author'])
print("Belief program detail page authors chart total (sum of all authors):", auth_exploded_belief.groupby('author')['media_id'].count().sum())
