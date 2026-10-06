with open('mem_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('port=5007', 'port=5008')

with open('mem_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
