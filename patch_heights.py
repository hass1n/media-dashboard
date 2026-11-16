import re
import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make all standard charts 280px height so they all fit on one screen
content = content.replace("margin=dict(l=20, r=20, t=40, b=40)", "height=280, margin=dict(l=20, r=20, t=40, b=40)")

# Fix the specific height=600 for the author images chart
content = content.replace("height=600,", "height=280,")
# Also reduce margins in that same block so the chart isn't mostly white space
content = content.replace("margin={'t': 120, 'b': 60}", "margin={'t': 60, 'b': 30}")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py heights to 280px")
