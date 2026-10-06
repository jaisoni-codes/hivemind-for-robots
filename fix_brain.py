with open('task_app_v3.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_logic = "available_robots = [r for r in self.robots if r.state in ('EXPLORING', 'IDLE')]"
good_logic = "available_robots = [r for r in self.robots if r.task is None]"

text = text.replace(bad_logic, good_logic)

with open('task_app_v4.py', 'w', encoding='utf-8') as f:
    f.write(text)
