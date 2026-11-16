import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace total_prog_sum
prog_old = '''    total_prog_sum = str(int(prog_counts['interviews'].sum())) if not prog_counts.empty else "0"'''
prog_new = '''    total_interviews_val = str(df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))]['media_id'].nunique())
    total_prog_sum = total_interviews_val'''
if prog_old in content:
    content = content.replace(prog_old, prog_new)
    print("Patched total_prog_sum")

# Replace total_outlet_sum
outlet_old = '''    total_outlet_sum = str(int(all_outlet_counts['interviews'].sum())) if not all_outlet_counts.empty else "0"'''
outlet_new = '''    total_outlet_sum = total_interviews_val'''
if outlet_old in content:
    content = content.replace(outlet_old, outlet_new)
    print("Patched total_outlet_sum")

# Replace output_impact block
out_old = '''    out_counts = out_exploded['output'].value_counts().reset_index()
    out_counts.columns = ['category', 'count']
    
    copies_sum_df = df[~df['media_id'].astype(str).str.startswith(('p', 'sm'))].drop_duplicates(subset=['media_id'])
    total_copies = pd.to_numeric(copies_sum_df['copies'], errors='coerce').fillna(0).sum()
    copies_df = pd.DataFrame([{'category': 'Total Distributed Copies', 'count': total_copies}])
    output_impact = pd.concat([out_counts, copies_df], ignore_index=True)
    
    total_out_sum = str(int(output_impact['count'].sum())) if not output_impact.empty else "0"'''

out_new = '''    exclude_list = ['economic update', 'research', 'conference', 'economic updates', 'economic news']
    out_exploded = out_exploded[~out_exploded['output'].str.lower().isin(exclude_list)]
    
    out_counts = out_exploded['output'].value_counts().reset_index()
    out_counts.columns = ['category', 'count']
    
    output_impact = out_counts
    
    total_out_sum = total_interviews_val'''

if out_old in content:
    content = content.replace(out_old, out_new)
    print("Patched output_impact")
else:
    print("Failed to patch output_impact")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
