import sys
import os
sys.path.append(os.path.abspath('.'))

import time
import math
import random
from hive_fastsim.simulator import Simulator, FastRobot, Human
from hive_dashboard.live_view import LiveDashboard
from hive_core.grid import OccupancyGrid, a_star

def run_scenario(seed=42, headless=False):
    random.seed(seed)
    
    width, height = 12.0, 12.0
    sim = Simulator(width, height)
    dashboard = None
    if not headless:
        dashboard = LiveDashboard(width, height)
    grid = OccupancyGrid(width, height)
    
    labels = ["fire_extinguisher", "toolbox", "pallet", "gas_cylinder", "first_aid_kit", 
              "ladder", "barrel", "cardboard_box", "safety_cone", "workbench", "electrical_panel"]
    for i in range(11):
        sim.add_object({'id': f'obj_{i}', 'label': labels[i], 'x': random.uniform(2, 10), 'y': random.uniform(2, 10)})
        
    for i in range(3):
        sim.add_human(Human(random.uniform(4, 8), random.uniform(4, 8)))
        
    # Docking bay positions to avoid spawn overlap
    for i in range(8):
        x = 0.5 + (i % 4) * 1.0
        y = 0.5 + (i // 4) * 1.0
        sim.add_robot(FastRobot(f'robot_{i}', x, y, 0.0))
        
    dt = 0.1
    # Increase max steps so they can finish 20 tasks
    for step in range(3000):
        if sim.tasks_completed >= 20:
            break

        if step % 20 == 0:
            for r in sim.robots:
                if not r.path:
                    goal = (random.uniform(2, 11), random.uniform(2, 11))
                    path = a_star(grid, (r.pose.x, r.pose.y), goal)
                    r.path = path
                    if path:
                        sim.tasks_completed += 1
                elif getattr(r, 'stuck_counter', 0) > 30:
                    # Stuck! Replan
                    goal = r.path[-1]
                    path = a_star(grid, (r.pose.x, r.pose.y), goal)
                    r.path = path
                    r.stuck_counter = 0
                        
        for i, r in enumerate(sim.robots):
            if not hasattr(r, 'stuck_counter'):
                r.stuck_counter = 0
                
            if r.path:
                target = r.path[0]
                dist = math.hypot(target[0] - r.pose.x, target[1] - r.pose.y)
                if dist < 0.2:
                    r.path.pop(0)
                    r.v = 0.0
                    r.w = 0.0
                    r.stuck_counter = 0
                else:
                    dx = target[0] - r.pose.x
                    dy = target[1] - r.pose.y
                    desired_heading = math.atan2(dy, dx)
                    heading_err = (desired_heading - r.pose.theta + math.pi) % (2 * math.pi) - math.pi
                    
                    r.w = max(-r.max_w, min(r.max_w, heading_err * 3.0))
                    r.v = max(0, min(r.max_v, dist * 1.0))
                    
                    if abs(heading_err) > 0.5:
                        r.v *= 0.2
                        
            # Basic collision avoidance & yield
            blocked = False
            for j, other in enumerate(sim.robots):
                if i != j:
                    d = math.hypot(other.pose.x - r.pose.x, other.pose.y - r.pose.y)
                    # Yield to lower ID if too close
                    if d < 1.2:
                        # Vector to other
                        dx = other.pose.x - r.pose.x
                        dy = other.pose.y - r.pose.y
                        angle_to = math.atan2(dy, dx)
                        angle_diff = abs((angle_to - r.pose.theta + math.pi) % (2*math.pi) - math.pi)
                        
                        if angle_diff < math.pi/2: # It's in front of me
                            if d < 0.7:
                                if i > j: # Higher ID yields
                                    r.v = -0.2 # Back up slowly
                                else:
                                    r.v = 0.0
                            else:
                                r.v *= 0.5
                            blocked = True
                            
            for h in sim.humans:
                d = math.hypot(h.x - r.pose.x, h.y - r.pose.y)
                if d < 1.5:
                    dx = h.x - r.pose.x
                    dy = h.y - r.pose.y
                    angle_to = math.atan2(dy, dx)
                    angle_diff = abs((angle_to - r.pose.theta + math.pi) % (2*math.pi) - math.pi)
                    if angle_diff < math.pi/2:
                        r.v = 0.0  
                        blocked = True
                        
            if blocked:
                r.stuck_counter += 1
            else:
                r.stuck_counter = max(0, r.stuck_counter - 1)
                    
        sim.step(dt)
        if not headless and step % 5 == 0:
            dashboard.update(sim)
            
    if not headless:
        import matplotlib.pyplot as plt
        plt.close('all')
        
    print(f"Scenario Finished (Seed {seed}). Tasks: {sim.tasks_completed}, Collisions: {sim.collisions}")
    return sim.tasks_completed, sim.collisions

if __name__ == '__main__':
    run_scenario(42)
