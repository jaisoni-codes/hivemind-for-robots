import time
import math
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.optimize import linear_sum_assignment
from hive_core.types import Task, RobotStatus, Pose2D
from hive_core.memory import LivingMemory

class Brain:
    def __init__(self, memory: LivingMemory = None):
        self.robots: Dict[str, RobotStatus] = {}
        self.tasks: Dict[str, Task] = {}
        self.assignments: Dict[str, str] = {}
        self.memory = memory
        
        self.heartbeat_timeout = 3.0
        self.task_counter = 0
        
    def update_robot_status(self, status: RobotStatus):
        self.robots[status.id] = status
        
    def add_task(self, task: Task):
        if task.id not in self.tasks:
            self.tasks[task.id] = task
            
    def remove_task(self, task_id: str):
        if task_id in self.tasks:
            del self.tasks[task_id]
        for r_id, t_id in list(self.assignments.items()):
            if t_id == task_id:
                del self.assignments[r_id]

    def _compute_eta(self, robot: RobotStatus, task: Task) -> float:
        if not task.target_pose:
            return 9999.0
        dist = math.hypot(robot.pose.x - task.target_pose.x, robot.pose.y - task.target_pose.y)
        return dist / 1.0
        
    def run_allocation(self, current_time: float):
        # 1. Fault Monitor
        dead_robots = []
        for r_id, status in self.robots.items():
            if current_time - status.timestamp > self.heartbeat_timeout:
                dead_robots.append(r_id)
                
        for r_id in dead_robots:
            if r_id in self.assignments:
                del self.assignments[r_id]
            del self.robots[r_id]

        available_robots = list(self.robots.keys())
        pending_tasks = [t for t in self.tasks.values()]
        
        if not available_robots or not pending_tasks:
            return
            
        cost_matrix = np.zeros((len(available_robots), len(pending_tasks)))
        for i, r_id in enumerate(available_robots):
            robot = self.robots[r_id]
            for j, task in enumerate(pending_tasks):
                eta = self._compute_eta(robot, task)
                if self.assignments.get(r_id) == task.id:
                    dist = math.hypot(robot.pose.x - task.target_pose.x, robot.pose.y - task.target_pose.y)
                    if dist > 1.5:
                        eta *= 0.85
                    else:
                        eta *= 0.01
                cost_matrix[i, j] = eta
                
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        new_assignments = {}
        for r_idx, t_idx in zip(row_ind, col_ind):
            r_id = available_robots[r_idx]
            t_id = pending_tasks[t_idx].id
            new_assignments[r_id] = t_id
            
        self.assignments = new_assignments

    def generate_curiosity_tasks(self):
        if not self.memory:
            return
        stale_records = [r for r in self.memory.get_all() if r.state == 'STALE']
        for r in stale_records:
            t_id = f"REFRESH_{r.id}"
            if t_id not in self.tasks:
                self.add_task(Task(id=t_id, type='REFRESH', priority=10, target_pose=r.pose))
