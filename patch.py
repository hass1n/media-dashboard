import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Patch fig_prog
prog_old = '''    fig_prog = px.bar(
        prog_counts,
        x='program',
        y='interviews',
        color='interviews',
        custom_data=['program'],  # Pass program name to Plotly event data
        title="Programs - Total Media Count",
        labels={'program': 'Program Name', 'interviews': 'Total Count'},'''

prog_new = '''    total_prog_sum = str(int(prog_counts['interviews'].sum())) if not prog_counts.empty else "0"
    fig_prog = px.bar(
        prog_counts,
        x='program',
        y='interviews',
        color='interviews',
        custom_data=['program'],  # Pass program name to Plotly event data
        title="Programs - Total Media Count",
        labels={'program': 'Program Name', 'interviews': total_prog_sum},'''

if prog_old in content:
    content = content.replace(prog_old, prog_new)
    print("Patched fig_prog")
else:
    print("Could not find fig_prog old content")

# 2. Patch fig_outlets_preview
out_prev_old = '''    fig_outlets_preview = px.bar(top_outlet_counts, x='outlet', y='interviews', color='interviews',
                                 title="Preview: Top Media Output",
                                 labels={'outlet': 'Media Output', 'interviews': 'Total Count'},'''

out_prev_new = '''    total_outlet_sum = str(int(all_outlet_counts['interviews'].sum())) if not all_outlet_counts.empty else "0"
    fig_outlets_preview = px.bar(top_outlet_counts, x='outlet', y='interviews', color='interviews',
                                 title="Preview: Top Media Output",
                                 labels={'outlet': 'Media Output', 'interviews': total_outlet_sum},'''

if out_prev_old in content:
    content = content.replace(out_prev_old, out_prev_new)
    print("Patched fig_outlets_preview")
else:
    print("Could not find fig_outlets_preview old content")

# 3. Patch fig_outlets_all
out_all_old = '''    fig_outlets_all = px.bar(all_outlet_counts, x='outlet', y='interviews', color='interviews',
                             title="All Media Output - Total Presence",
                             labels={'outlet': 'Media Output', 'interviews': 'Total Count'},'''

out_all_new = '''    fig_outlets_all = px.bar(all_outlet_counts, x='outlet', y='interviews', color='interviews',
                             title="All Media Output - Total Presence",
                             labels={'outlet': 'Media Output', 'interviews': total_outlet_sum},'''

if out_all_old in content:
    content = content.replace(out_all_old, out_all_new)
    print("Patched fig_outlets_all")
else:
    print("Could not find fig_outlets_all old content")

# 4. Patch fig_outlets_all yaxis_title
out_all_y_old = '''xaxis={'automargin': True}, yaxis_title="Total Count")'''
out_all_y_new = '''xaxis={'automargin': True}, yaxis_title=total_outlet_sum)'''

if out_all_y_old in content:
    content = content.replace(out_all_y_old, out_all_y_new)
    print("Patched fig_outlets_all yaxis")
else:
    print("Could not find fig_outlets_all yaxis old content")

# 5. Patch fig_out
out_old = '''    fig_out = px.bar(output_impact, x='category', y='count', color='category',
                     title="Output Type & Distribution Impact",
                     labels={'category': 'Output Category', 'count': 'Quantity'},'''

out_new = '''    total_out_sum = str(int(output_impact['count'].sum())) if not output_impact.empty else "0"
    fig_out = px.bar(output_impact, x='category', y='count', color='category',
                     title="Output Type & Distribution Impact",
                     labels={'category': 'Output Category', 'count': total_out_sum},'''

if out_old in content:
    content = content.replace(out_old, out_new)
    print("Patched fig_out")
else:
    print("Could not find fig_out old content")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
