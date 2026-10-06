with open('perc_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('port=5009', 'port=5010')

with open('perc_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
