import sys
import os
sys.path.append(os.path.abspath('.'))

import time
from hive_core.brain import Brain
from hive_core.memory import LivingMemory
from hive_core.types import Task, RobotStatus, Pose2D, Detection

def test_m3_brain_allocation_and_fault():
    brain = Brain()
    
    now = time.time()
    brain.update_robot_status(RobotStatus(id="r1", pose=Pose2D(0, 0, 0), velocity=(0,0), current_task_id=None, state="IDLE", timestamp=now))
    brain.update_robot_status(RobotStatus(id="r2", pose=Pose2D(0, 10, 0), velocity=(0,0), current_task_id=None, state="IDLE", timestamp=now))
    brain.update_robot_status(RobotStatus(id="r3", pose=Pose2D(10, 0, 0), velocity=(0,0), current_task_id=None, state="IDLE", timestamp=now))
    brain.update_robot_status(RobotStatus(id="r4", pose=Pose2D(10, 10, 0), velocity=(0,0), current_task_id=None, state="IDLE", timestamp=now))
    
    brain.add_task(Task(id="t1", type="INSPECT", priority=1, target_pose=Pose2D(1, 1, 0)))
    
    brain.run_allocation(now)
    
    assert brain.assignments.get("r1") == "t1"
    
    brain.update_robot_status(RobotStatus(id="r2", pose=Pose2D(0, 10, 0), velocity=(0,0), current_task_id=None, state="IDLE", timestamp=now + 5))
    brain.update_robot_status(RobotStatus(id="r3", pose=Pose2D(10, 0, 0), velocity=(0,0), current_task_id=None, state="IDLE", timestamp=now + 5))
    brain.update_robot_status(RobotStatus(id="r4", pose=Pose2D(10, 10, 0), velocity=(0,0), current_task_id=None, state="IDLE", timestamp=now + 5))
    
    brain.run_allocation(now + 5)
    
    assert "r1" not in brain.robots
    assert "r1" not in brain.assignments
    assert "t1" in brain.assignments.values()
    
def test_m3_curiosity():
    mem = LivingMemory()
    brain = Brain(memory=mem)
    
    mem.ingest_detection(Detection('pallet', 1.0, 0.0, 1.0, x=5, y=5, timestamp=time.time() - 900), 'r1')
    mem.update_decay(time.time())
    
    assert mem.get_all()[0].state == 'STALE'
    
    brain.generate_curiosity_tasks()
    
    refresh_tasks = [t for t in brain.tasks.values() if t.type == 'REFRESH']
    assert len(refresh_tasks) == 1
    assert refresh_tasks[0].target_pose.x == 5.0
