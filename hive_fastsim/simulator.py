import numpy as np
import math
import pickle
import os
from typing import List, Tuple, Dict, Any
from hive_core.types import Pose2D
from hive_core.config import is_enabled

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
        self.battery_level = 100.0

    def update(self, dt: float):
        self.pose.theta += self.w * dt
        self.pose.theta = (self.pose.theta + math.pi) % (2 * math.pi) - math.pi
        self.pose.x += self.v * math.cos(self.pose.theta) * dt
        self.pose.y += self.v * math.sin(self.pose.theta) * dt
        # Drain battery slightly
        self.battery_level -= 0.01 * dt * (abs(self.v) + 0.1)

class Human:
    def __init__(self, obj_id: str, x: float, y: float, is_dynamic=True):
        self.id = obj_id
        self.x = x
        self.y = y
        self.v = 0.5 if is_dynamic else 0.0
        self.theta = np.random.uniform(-math.pi, math.pi) if is_dynamic else 0.0
        self.radius = 0.3
        self.is_dynamic = is_dynamic

    def update(self, dt: float, width: float, height: float, robots: List[FastRobot]):
        if not self.is_dynamic:
            return
            
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
            
        for r in robots:
            if math.hypot(nx - r.pose.x, ny - r.pose.y) < (self.radius + r.radius):
                self.theta = math.pi - self.theta
                nx = self.x
                ny = self.y
                break
                
        self.x = nx
        self.y = ny

class MockCameraDetector:
    def __init__(self):
        self.model = None
        if os.path.exists('hive_ml/detector.pkl'):
            with open('hive_ml/detector.pkl', 'rb') as f:
                self.model = pickle.load(f)
                
        self.base_vectors = {
            'fire_extinguisher': np.array([5.0]*32),
            'pallet': np.array([-2.0]*32),
            'toolbox': np.array([0.5]*32),
            'human': np.array([8.0]*32),
            'forklift': np.array([-6.0]*32),
        }
        self.classes = ['fire_extinguisher', 'pallet', 'toolbox', 'human', 'forklift']

    def detect(self, true_label: str) -> Tuple[str, float]:
        if not is_enabled('detector'): 
            return true_label, 1.0 
            
        if self.model is None or true_label not in self.base_vectors:
            return true_label, 1.0
            
        base = self.base_vectors[true_label]
        noise = np.random.normal(0, 2.5, 32)
        feature = base + noise
        
        pred_idx = self.model.predict([feature])[0]
        prob = np.max(self.model.predict_proba([feature])[0])
        
        return self.classes[pred_idx], prob

class Simulator:
    def __init__(self, width: float=20.0, height: float=20.0):
        self.width = width
        self.height = height
        self.robots: List[FastRobot] = []
        self.humans: List[Human] = [] # Acts as dynamic/static obstacles
        self.objects: Dict[str, Dict[str, Any]] = {} # id -> data
        self.tasks_completed = 0
        self.collisions = 0
        self.time = 0.0
        self.camera = MockCameraDetector()
        
    def add_robot(self, robot: FastRobot):
        self.robots.append(robot)
        
    def add_human(self, human: Human):
        self.humans.append(human)
        
    def add_dynamic_object(self, op: Dict):
        obj_id = op['id']
        self.objects[obj_id] = op
        pose = op['pose']
        # If it's a human/forklift, add to physical bodies
        if op.get('class') in ['human', 'forklift']:
            self.humans.append(Human(obj_id, pose[0], pose[1], is_dynamic=True))
        elif op.get('class') == 'pallet' or op.get('class') == 'box':
            self.humans.append(Human(obj_id, pose[0], pose[1], is_dynamic=False)) # Static obstacle

    def move_dynamic_object(self, op: Dict):
        obj_id = op['id']
        if obj_id in self.objects:
            self.objects[obj_id]['pose'] = op['pose']
        for h in self.humans:
            if h.id == obj_id:
                h.x = op['pose'][0]
                h.y = op['pose'][1]

    def remove_dynamic_object(self, obj_id: str):
        if obj_id in self.objects:
            del self.objects[obj_id]
        self.humans = [h for h in self.humans if h.id != obj_id]

    def step(self, dt: float):
        self.time += dt
        for robot in self.robots:
            robot.update(dt)
        for human in self.humans:
            human.update(dt, self.width, self.height, self.robots)
            
        self.check_collisions()

    def check_collisions(self):
        for i, r in enumerate(self.robots):
            for j in range(i+1, len(self.robots)):
                r2 = self.robots[j]
                if math.hypot(r.pose.x - r2.pose.x, r.pose.y - r2.pose.y) < (r.radius + r2.radius):
                    self.collisions += 1
            for h in self.humans:
                if math.hypot(r.pose.x - h.x, r.pose.y - h.y) < (r.radius + h.radius):
                    self.collisions += 1
