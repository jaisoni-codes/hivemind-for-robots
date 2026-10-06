with open('task_app_v4.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('port=5014', 'port=5015')
with open('task_app_v4.py', 'w', encoding='utf-8') as f:
    f.write(text)
