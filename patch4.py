import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make the label string
label_str = 'f"Total Count: {total_interviews_val}"'

# 1. Update Programs
prog_old = '''labels={'program': 'Program Name', 'interviews': total_prog_sum},'''
prog_new = '''labels={'program': 'Program Name', 'interviews': f"Total Count: {total_prog_sum}"},'''
content = content.replace(prog_old, prog_new)

# 2. Update Output Type (fig_out)
out_old = '''labels={'category': 'Output Category', 'count': total_out_sum},'''
out_new = '''labels={'category': 'Output Category', 'count': f"Total Count: {total_out_sum}"},'''
content = content.replace(out_old, out_new)

# 3. Update Media Preview
prev_old = '''labels={'outlet': 'Media Output', 'interviews': total_outlet_sum},'''
prev_new = '''labels={'outlet': 'Media Output', 'interviews': f"Total Count: {total_outlet_sum}"},'''
content = content.replace(prev_old, prev_new)

# 4. Update Media All yaxis
all_y_old = '''xaxis={'automargin': True}, yaxis_title=total_outlet_sum)'''
all_y_new = '''xaxis={'automargin': True}, yaxis_title=f"Total Count: {total_outlet_sum}")'''
content = content.replace(all_y_old, all_y_new)

# 5. Update Authors
# Note: we haven't updated Authors to use total_interviews_val yet.
auth_old = '''    fig_auth = px.bar(auth_counts, x='author', y='interviews', color='interviews',
                      title="Number of interviews per authors",
                      labels={'author': 'Author', 'interviews': 'Total Count'},'''

auth_new = '''    total_auth_sum = total_interviews_val
    fig_auth = px.bar(auth_counts, x='author', y='interviews', color='interviews',
                      title="Number of interviews per authors",
                      labels={'author': 'Author', 'interviews': f"Total Count: {total_auth_sum}"},'''
content = content.replace(auth_old, auth_new)


with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
