with open('ultimate_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('return HTML_TEMPLATE', 'return HTML')

with open('ultimate_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
