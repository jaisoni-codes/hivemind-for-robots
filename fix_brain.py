import sys
import os
sys.path.append(os.path.abspath('.'))

with open('hive_core/brain.py', 'r') as f:
    content = f.read()

content = content.replace(
'''            elif current_time - r.timestamp > 3.0:
                # Dead robot
                t_id = self.tasks.robot_assignments.get(r_id)''',
'''            elif current_time - r.timestamp > 3.0:
                # Dead robot
                r.state = "DEAD"
                t_id = self.tasks.robot_assignments.get(r_id)'''
)

content = content.replace(
'''        unassigned_robots = [r_id for r_id, r in self.robots.items() if r_id not in self.tasks.robot_assignments and r.state != "DOCKING"]''',
'''        unassigned_robots = [r_id for r_id, r in self.robots.items() if r_id not in self.tasks.robot_assignments and r.state not in ["DOCKING", "DEAD"]]'''
)

with open('hive_core/brain.py', 'w') as f:
    f.write(content)
