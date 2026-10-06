import sys
import os
sys.path.append(os.path.abspath('.'))
import time
from hive_core.brain import Brain
from hive_core.types import Task, RobotStatus, Pose2D

brain = Brain()
now = time.time()
r1 = RobotStatus(id="r1", pose=Pose2D(0, 0, 0), velocity=(0,0), current_task_id=None, state="IDLE", timestamp=now)
brain.update_robot_status(r1)
brain.tasks.add_task(Task(id="t1", type="INSPECT", priority=1, target_pose=Pose2D(1, 1, 0)))

brain.allocate()
print(f"After allocation 1: {brain.tasks.robot_assignments}")

brain.robots["r1"].timestamp = time.time() - 5.0
brain.last_allocation_time = 0.0

brain.allocate()
print(f"After allocation 2: {brain.tasks.robot_assignments}")
