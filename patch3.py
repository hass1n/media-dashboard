import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Filter the main df
df_filter_old = '''    # Standardize media names across the dataset
    df['media_source'] = df['media_source'].apply(standardize_media_name)
    df['weight'] = 1  # Standard flat weight for all counts

    # --- Chart 1: Programs Bar Chart (All Media) ---'''

df_filter_new = '''    # Standardize media names across the dataset
    df['media_source'] = df['media_source'].apply(standardize_media_name)
    df['weight'] = 1  # Standard flat weight for all counts
    
    # Filter out unwanted outputs entirely from the dashboard
    exclude_list = ['economic update', 'research', 'conference', 'economic updates', 'economic news']
    def should_exclude(val):
        if pd.isna(val): return False
        parts = [p.strip().lower() for p in str(val).split(',')]
        return any(p in exclude_list for p in parts)
    
    df = df[~df['output'].apply(should_exclude)]

    # --- Chart 1: Programs Bar Chart (All Media) ---'''

if df_filter_old in content:
    content = content.replace(df_filter_old, df_filter_new)
    print("Patched df filter")
else:
    print("Failed to patch df filter")

# 2. Change titles
replacements = {
    'title="Programs - Total Media Count"': 'title="Numbers of interviews per programs"',
    'title="Output Type & Distribution Impact"': 'title="Number of interviews per media type"',
    'title="Preview: Top Media Output"': 'title="Numbers of interviews per media channel"',
    'title="All Media Output - Total Presence"': 'title="Numbers of interviews per media channel - All"',
    'title="Top Authors - Total Presence"': 'title="Number of interviews per authors"'
}

for old, new in replacements.items():
    if old in content:
        content = content.replace(old, new)
        print(f"Patched {old}")
    else:
        print(f"Failed to patch {old}")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
