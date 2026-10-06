with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
# Fix powershell destroying javascript string interpolation variables
text = text.replace('\', '')
text = text.replace('\', '')
text = text.replace('\', '')
text = text.replace('\', '')
text = text.replace('\', '')
text = text.replace('\', '')
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
