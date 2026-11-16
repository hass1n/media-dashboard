import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update total_prog_sum (1st chart)
content = content.replace(
    '''total_prog_sum = total_interviews_val''', 
    '''total_prog_sum = str(int(prog_counts['interviews'].sum())) if not prog_counts.empty else "0"'''
)
content = content.replace(
    '''labels={'program': 'Program Name', 'interviews': f"Total Count: {total_prog_sum}"},''',
    '''labels={'program': 'Program Name', 'interviews': total_prog_sum},'''
)

# 2. Update total_outlet_sum (3rd chart)
content = content.replace(
    '''total_outlet_sum = total_interviews_val''', 
    '''total_outlet_sum = str(int(all_outlet_counts['interviews'].sum())) if not all_outlet_counts.empty else "0"'''
)
content = content.replace(
    '''labels={'outlet': 'Media Output', 'interviews': f"Total Count: {total_outlet_sum}"},''',
    '''labels={'outlet': 'Media Output', 'interviews': total_outlet_sum},'''
)
content = content.replace(
    '''yaxis_title=f"Total Count: {total_outlet_sum}")''',
    '''yaxis_title=total_outlet_sum)'''
)

# 3. Update total_out_sum (2nd chart)
content = content.replace(
    '''total_out_sum = total_interviews_val''', 
    '''total_out_sum = str(int(output_impact['count'].sum())) if not output_impact.empty else "0"'''
)

# 4. Update total_auth_sum (Author chart)
content = content.replace(
    '''total_auth_sum = total_interviews_val''', 
    '''total_auth_sum = str(int(auth_counts['interviews'].sum())) if not auth_counts.empty else "0"'''
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
