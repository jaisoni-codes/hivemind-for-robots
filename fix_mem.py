with open('mem_app.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('\', '')
text = text.replace('\', '')
text = text.replace('\', '')
text = text.replace('return HTML_TEMPLATE', 'return HTML')
with open('mem_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
