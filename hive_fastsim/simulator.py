import numpy as np
import math
from typing import List, Tuple, Dict
from hive_core.types import Pose2D

class FastRobot:
    def __init__(self, robot_id: str, x: float, y: float, theta: float):
        self.id = robot_id
        self.pose = Pose2D(x, y, theta)
        self.radius = 0.3
        self.v = 0.0
        self.w = 0.0
        self.max_v = 1.0
        self.max_w = 2.0
        self.path = []

    def update(self, dt: float):
        self.pose.theta += self.w * dt
        self.pose.theta = (self.pose.theta + math.pi) % (2 * math.pi) - math.pi
        self.pose.x += self.v * math.cos(self.pose.theta) * dt
        self.pose.y += self.v * math.sin(self.pose.theta) * dt

class Human:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.v = 0.5
        self.theta = np.random.uniform(-math.pi, math.pi)
        self.radius = 0.3

    def update(self, dt: float, width: float, height: float, robots: List[FastRobot]):
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
            
        # Humans bounce off stopped robots (but if robot moves into human, collision counts below)
        for r in robots:
            if math.hypot(nx - r.pose.x, ny - r.pose.y) < (self.radius + r.radius):
                self.theta = math.pi - self.theta # Bounce
                nx = self.x
                ny = self.y
                break
                
        self.x = nx
        self.y = ny

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
        for robot in self.robots:
            robot.update(dt)
        for human in self.humans:
            human.update(dt, self.width, self.height, self.robots)
            
        self.check_collisions()

    def check_collisions(self):
        # Allow overlaps but count them
        for i, r in enumerate(self.robots):
            for j in range(i+1, len(self.robots)):
                r2 = self.robots[j]
                if math.hypot(r.pose.x - r2.pose.x, r.pose.y - r2.pose.y) < (r.radius + r2.radius):
                    self.collisions += 1
            for h in self.humans:
                if math.hypot(r.pose.x - h.x, r.pose.y - h.y) < (r.radius + h.radius):
                    self.collisions += 1
