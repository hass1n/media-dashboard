import re
import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's replace the specific heights found in Select-String, but only in update_layout
# We'll use a regex that matches .update_layout(...) and modifies inside.
def replacer(match):
    text = match.group(0)
    # Remove height=XXX
    text = re.sub(r'height=\d+,\s*', '', text)
    text = re.sub(r',\s*height=\d+', '', text)
    # Change fonts
    text = text.replace("title={'font': {'size': 20}}", "title={'font': {'size': 14}}")
    text = text.replace("xaxis={'tickfont': {'size': 12}, 'title': {'font': {'size': 14}}}", "xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}}")
    text = text.replace("yaxis={'tickfont': {'size': 12}, 'title': {'font': {'size': 14}}}", "yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}}")
    
    # If there's no margin, we could add it, but removing height might be enough for it to autosize properly within the flex container.
    return text

# Match fig_XXX.update_layout( ... )
# We only want to match the ones we saw. We'll just run the replacer on the whole file, but carefully.
# Actually, a simpler way is to just do simple string replacements.

replacements = [
    ("height=550,", "margin=dict(l=20, r=20, t=40, b=40),"),
    ("height=500,", "margin=dict(l=20, r=20, t=40, b=40),"),
    ("height=450,", "margin=dict(l=20, r=20, t=40, b=40),"),
    ("height=700,", ""), # for outlets all, let it autosize or stay as is? We'll remove it.
    ("title={'font': {'size': 20}}", "title={'font': {'size': 14}}"),
    ("xaxis={'tickfont': {'size': 12}, 'title': {'font': {'size': 14}}}", "xaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}}"),
    ("yaxis={'tickfont': {'size': 12}, 'title': {'font': {'size': 14}}}", "yaxis={'tickfont': {'size': 10}, 'title': {'font': {'size': 11}}}")
]

for old, new in replacements:
    content = content.replace(old, new)

# Fix any stray height=500 at the end of the line before a closing parenthesis if any
content = re.sub(r',\s*height=\d+\)', ')', content)
content = re.sub(r'height=\d+\)', ')', content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py")
