import re

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all instances
new_content = content.replace('use_container_width=True', 'width="stretch"')

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('✅ Replaced all use_container_width=True with width="stretch"')
