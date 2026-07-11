import re
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()
count = content.count('use_container_width')
fixed = content.replace('use_container_width=True', 'width="stretch"')
fixed = fixed.replace('use_container_width=False', 'width="content"')
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(fixed)
print(f"Fixed {count} occurrences")
