import numpy as np
import math
from typing import List, Tuple, Dict
from hive_core.types import Pose2D, Task, RobotStatus

class FastRobot:
    def __init__(self, robot_id: str, x: float, y: float, theta: float):
        self.id = robot_id
        self.pose = Pose2D(x, y, theta)
        self.radius = 0.3
        self.v = 0.0
        self.w = 0.0
        self.max_v = 1.0
        self.max_w = 2.0
        self.task = None
        self.path = []

    def get_next_pose(self, dt: float) -> Tuple[float, float, float]:
        ntheta = self.pose.theta + self.w * dt
        ntheta = (ntheta + math.pi) % (2 * math.pi) - math.pi
        nx = self.pose.x + self.v * math.cos(self.pose.theta) * dt
        ny = self.pose.y + self.v * math.sin(self.pose.theta) * dt
        return nx, ny, ntheta

class Human:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.v = 0.5
        self.theta = np.random.uniform(-math.pi, math.pi)
        self.radius = 0.3

    def get_next_pose(self, dt: float, width: float, height: float):
        if np.random.rand() < 0.05:
            self.theta += np.random.uniform(-1, 1)
        nx = self.x + self.v * math.cos(self.theta) * dt
        ny = self.y + self.v * math.sin(self.theta) * dt
        
        if nx < 0 or nx > width:
            self.theta = math.pi - self.theta
            nx = self.x
        if ny < 0 or ny > height:
            self.theta = -self.theta
            ny = self.y
            
        return nx, ny

class Simulator:
    def __init__(self, width: float=12.0, height: float=12.0):
        self.width = width
        self.height = height
        self.robots: List[FastRobot] = []
        self.humans: List[Human] = []
        self.objects: List[Dict] = []
        self.tasks_completed = 0
        self.collisions = 0
        self.time = 0.0
        
    def add_robot(self, robot: FastRobot):
        self.robots.append(robot)
        
    def add_human(self, human: Human):
        self.humans.append(human)
        
    def add_object(self, obj: Dict):
        self.objects.append(obj)
        
    def step(self, dt: float):
        self.time += dt
        
        # Tentative moves
        r_next = [r.get_next_pose(dt) for r in self.robots]
        h_next = [h.get_next_pose(dt, self.width, self.height) for h in self.humans]
        
        # Perfect Shield: if moving causes overlap, don't move
        for i, r in enumerate(self.robots):
            nx, ny, ntheta = r_next[i]
            blocked = False
            for j, r2 in enumerate(self.robots):
                if i != j:
                    ox, oy, _ = r_next[j]
                    if math.hypot(nx - ox, ny - oy) < (r.radius + r2.radius):
                        blocked = True
                        break
            for j, h in enumerate(self.humans):
                hx, hy = h_next[j]
                if math.hypot(nx - hx, ny - hy) < (r.radius + h.radius + 0.1):
                    blocked = True
                    break
            
            if not blocked:
                r.pose.x = nx
                r.pose.y = ny
                r.pose.theta = ntheta
            else:
                # Still rotate, just don't translate
                r.pose.theta = ntheta
                
        for i, h in enumerate(self.humans):
            hx, hy = h_next[i]
            blocked = False
            for r in self.robots:
                if math.hypot(hx - r.pose.x, hy - r.pose.y) < (h.radius + r.radius):
                    blocked = True
                    h.theta = (h.theta + math.pi) % (2*math.pi) - math.pi
                    break
            if not blocked:
                h.x = hx
                h.y = hy
