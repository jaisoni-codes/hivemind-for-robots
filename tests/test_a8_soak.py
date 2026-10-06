import sys
import os
sys.path.append(os.path.abspath('.'))
from hive_core.config import Config
from hive_core.logger import BlackBoxLogger
from hive_core.types import RobotStatus, Pose2D, Task
from hive_core.brain import Brain
import time

def test_a8_battery_and_logging():
    Config.load('hivemind')
    brain = Brain()
    
    # 1. Test battery docking
    r1 = RobotStatus(id='r1', pose=Pose2D(5,5,0), velocity=(0,0), current_task_id=None, state="IDLE", battery_level=15.0)
    brain.update_robot_status(r1)
    
    # Add a normal task
    brain.tasks.add_task(Task(id='t1', type='GOTO', priority=1, target_pose=Pose2D(8,8,0)))
    
    brain.allocate()
    
    # Because battery is 15.0 (<20), it should be docking, NOT getting t1
    assert brain.robots['r1'].state == "DOCKING"
    assert 't1' not in brain.tasks.active_tasks, "t1 should not be assigned to low battery robot"
    
def test_a8_soak_memory_bound():
    logger = BlackBoxLogger(log_dir="logs_test")
    logger.max_lines = 100
    
    for i in range(250):
        logger.log_event("TEST", "SOAK", {"iteration": i})
        
    files = os.listdir("logs_test")
    assert len(files) >= 2, "Logger didn't rotate files"
