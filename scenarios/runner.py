import sys
import os
sys.path.append(os.path.abspath('.'))

import time
import math
import random
import numpy as np
from typing import Tuple
from hive_fastsim.simulator import Simulator, FastRobot, Human
from hive_dashboard.live_view import LiveDashboard
from hive_core.grid import OccupancyGrid, a_star
from hive_core.tracker import Tracker
from hive_core.shield import SafetyShield
from hive_core.types import Pose2D

def run_scenario(seed=42, headless=False, use_shield=True, num_robots=4, target_tasks=10) -> Tuple[int, int, float]:
    random.seed(seed)
    np.random.seed(seed)
    
    width, height = 20.0, 20.0 # larger to fit 32 robots
    sim = Simulator(width, height)
    dashboard = None
    if not headless:
        dashboard = LiveDashboard(width, height)
    grid = OccupancyGrid(width, height)
    tracker = Tracker()
    shield = SafetyShield()
    
    for i in range(5):
        sim.add_human(Human(random.uniform(4, 16), random.uniform(4, 16)))
        
    for i in range(num_robots): 
        x = 0.5 + (i % 8) * 1.5
        y = 0.5 + (i // 8) * 1.5
        sim.add_robot(FastRobot(f'robot_{i}', x, y, 0.0))
        
    dt = 0.1
    start_time = time.time()
    steps_taken = 0
    for step in range(3000):
        if sim.tasks_completed >= target_tasks:
            break
        steps_taken += 1

        detections = []
        for h in sim.humans:
            detections.append((h.x, h.y))
        tracker.process_detections(detections, sim.time)
        predictions = tracker.get_predictions(horizon_s=2.0, steps=4)

        if step % 20 == 0:
            for r in sim.robots:
                if not r.path:
                    goal = (random.uniform(2, 18), random.uniform(2, 18))
                    r.path = a_star(grid, (r.pose.x, r.pose.y), goal)
                    if r.path:
                        sim.tasks_completed += 1
                        
        for i, r in enumerate(sim.robots):
            target_v = 0.0
            target_w = 0.0
            
            if r.path:
                target = r.path[0]
                dist = math.hypot(target[0] - r.pose.x, target[1] - r.pose.y)
                if dist < 0.3:
                    r.path.pop(0)
                else:
                    dx = target[0] - r.pose.x
                    dy = target[1] - r.pose.y
                    desired_heading = math.atan2(dy, dx)
                    heading_err = (desired_heading - r.pose.theta + math.pi) % (2 * math.pi) - math.pi
                    
                    target_w = max(-r.max_w, min(r.max_w, heading_err * 3.0))
                    target_v = max(0, min(r.max_v, dist * 1.0))
                    
                    if abs(heading_err) > 0.5:
                        target_v *= 0.2

            other_robots = [or_r.pose for j, or_r in enumerate(sim.robots) if i != j]
            r.v, r.w = shield.compute_safe_velocity(r.pose, target_v, target_w, predictions, other_robots, use_shield=use_shield)
                    
        sim.step(dt)
        if not headless and step % 5 == 0:
            dashboard.update(sim)
            
    if not headless:
        import matplotlib.pyplot as plt
        plt.close('all')
        
    sim_duration = steps_taken * dt
    # print(f"Scenario Seed {seed} | Shield {use_shield} | Robots {num_robots} | Tasks: {sim.tasks_completed} | Collisions: {sim.collisions} | Time: {sim_duration:.1f}s")
    return sim.tasks_completed, sim.collisions, sim_duration

if __name__ == '__main__':
    run_scenario(42, use_shield=True)
