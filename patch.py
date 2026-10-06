with open('mem_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_logic = '''        if self.target is None or (len(self.path) == 0 and math.hypot(self.target[0]-self.x, self.target[1]-self.y) < 1.0):
            self.target = (random.uniform(3, 17), random.uniform(3, 17))
            self.replan()
            self.state = 'MOVING' '''

good_logic = '''        if self.target is None or len(self.path) == 0:
            for _ in range(10):
                self.target = (random.uniform(2, 18), random.uniform(2, 18))
                self.replan()
                if len(self.path) > 0: break
            self.state = 'MOVING' '''

text = text.replace(bad_logic, good_logic)

with open('mem_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
