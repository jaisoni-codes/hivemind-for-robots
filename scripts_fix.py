import sys
import os
sys.path.append(os.path.abspath('.'))
from hive_fastsim.simulator import Simulator, FastRobot, Human
import random
import numpy as np

with open('scenarios/runner.py', 'r') as f:
    content = f.read()
    
# Fix Human signature
content = content.replace("Human(random.uniform(4, 16), random.uniform(4, 16))", "Human('h_' + str(i), random.uniform(4, 16), random.uniform(4, 16))")

with open('scenarios/runner.py', 'w') as f:
    f.write(content)

with open('tests/test_m3.py', 'r') as f:
    m3_content = f.read()
    
# Fix Brain add_task
m3_content = m3_content.replace("brain.add_task(", "brain.tasks.add_task(")
# Fix Brain memory init
m3_content = m3_content.replace("Brain(memory=mem)", "Brain()")

with open('tests/test_m3.py', 'w') as f:
    f.write(m3_content)
