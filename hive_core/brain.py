import time
import math
import numpy as np
from typing import Dict, List, Optional
from scipy.optimize import linear_sum_assignment
from hive_core.types import Task, RobotStatus, Pose2D
from hive_core.logger import BlackBoxLogger
from hive_core.config import is_enabled

class TaskManager:
    def __init__(self):
        self.queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {} # task_id -> Task
        self.robot_assignments: Dict[str, str] = {} # robot_id -> task_id
        
    def add_task(self, task: Task):
        self.queue.append(task)
        self.queue.sort(key=lambda t: t.priority, reverse=True)

class Brain:
    def __init__(self):
        self.tasks = TaskManager()
        self.robots: Dict[str, RobotStatus] = {}
        self.last_allocation_time = 0
        self.allocation_interval = 2.0
        self.logger = BlackBoxLogger()
        self.dock_pose = Pose2D(1.0, 1.0, 0.0)
        
    def update_robot_status(self, status: RobotStatus):
        self.robots[status.id] = status
        
    def _compute_eta(self, robot: RobotStatus, task: Task) -> float:
        if not task.target_pose:
            return 999.0
            
        dist = math.hypot(task.target_pose.x - robot.pose.x, task.target_pose.y - robot.pose.y)
        eta = dist / 1.0 # 1.0 m/s max speed
        
        # A8: Battery-aware allocation
        if is_enabled('battery_aware'):
            if robot.battery_level < 30.0:
                eta += (30.0 - robot.battery_level) * 5.0 # Heavy penalty for low battery
        return eta

    def allocate(self):
        current_time = time.time()
        
        # Monitor for dead robots or low battery
        for r_id, r in list(self.robots.items()):
            # A8: Battery check
            if is_enabled('battery_aware') and r.battery_level < 20.0 and r.state != "DOCKING":
                r.state = "DOCKING"
                t_id = self.tasks.robot_assignments.get(r_id)
                if t_id:
                    task = self.tasks.active_tasks.pop(t_id)
                    task.assigned_robot = None
                    self.tasks.queue.append(task) # Re-queue
                    del self.tasks.robot_assignments[r_id]
                    self.logger.log_event("REASSIGN", "BATTERY_LOW", {"robot": r_id, "task": t_id})
                
                # Assign dock task
                dock_task = Task(f"dock_{r_id}", "RETURN_TO_DOCK", 99, self.dock_pose)
                dock_task.assigned_robot = r_id
                self.tasks.active_tasks[dock_task.id] = dock_task
                self.tasks.robot_assignments[r_id] = dock_task.id
                
            # Fault Monitor
            elif current_time - r.timestamp > 3.0:
                # Dead robot
                t_id = self.tasks.robot_assignments.get(r_id)
                if t_id:
                    task = self.tasks.active_tasks.pop(t_id)
                    task.assigned_robot = None
                    self.tasks.queue.append(task)
                    del self.tasks.robot_assignments[r_id]
                    self.logger.log_event("REASSIGN", "ROBOT_DEAD", {"robot": r_id, "task": t_id})
        
        if current_time - self.last_allocation_time < self.allocation_interval:
            return
            
        self.last_allocation_time = current_time
        
        unassigned_robots = [r_id for r_id, r in self.robots.items() if r_id not in self.tasks.robot_assignments and r.state != "DOCKING"]
        if not unassigned_robots or not self.tasks.queue:
            return
            
        tasks_to_assign = self.tasks.queue[:len(unassigned_robots)]
        
        cost_matrix = np.zeros((len(unassigned_robots), len(tasks_to_assign)))
        for i, r_id in enumerate(unassigned_robots):
            for j, task in enumerate(tasks_to_assign):
                cost_matrix[i, j] = self._compute_eta(self.robots[r_id], task)
                
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        tasks_assigned = []
        for i, j in zip(row_ind, col_ind):
            r_id = unassigned_robots[i]
            task = tasks_to_assign[j]
            task.assigned_robot = r_id
            self.tasks.active_tasks[task.id] = task
            self.tasks.robot_assignments[r_id] = task.id
            tasks_assigned.append(task)
            self.logger.log_event("ASSIGN", "ETA_OPTIMAL", {"robot": r_id, "task": task.id})
            
        for t in tasks_assigned:
            self.tasks.queue.remove(t)
