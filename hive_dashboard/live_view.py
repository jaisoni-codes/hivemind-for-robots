import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

class LiveDashboard:
    def __init__(self, width: float, height: float):
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.width = width
        self.height = height
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.set_aspect('equal')
        self.ax.set_title("HIVEMIND Live Dashboard")
        
        self.robot_patches = {}
        self.human_patches = {}
        self.object_patches = {}

    def update(self, sim):
        self.ax.clear()
        self.ax.set_xlim(0, self.width)
        self.ax.set_ylim(0, self.height)
        self.ax.set_title(f"Tasks Completed: {sim.tasks_completed} | Collisions: {sim.collisions} | Time: {sim.time:.1f}s")
        
        # Draw objects
        for obj in sim.objects:
            c = plt.Circle((obj['x'], obj['y']), 0.2, color='gray')
            self.ax.add_patch(c)
            self.ax.text(obj['x'], obj['y'], obj['label'], fontsize=8)
            
        # Draw humans
        for i, h in enumerate(sim.humans):
            c = plt.Circle((h.x, h.y), h.radius, color='red', alpha=0.5)
            self.ax.add_patch(c)
            
        # Draw robots
        for r in sim.robots:
            c = plt.Circle((r.pose.x, r.pose.y), r.radius, color='blue', alpha=0.7)
            self.ax.add_patch(c)
            # heading
            hx = r.pose.x + r.radius * math.cos(r.pose.theta)
            hy = r.pose.y + r.radius * math.sin(r.pose.theta)
            self.ax.plot([r.pose.x, hx], [r.pose.y, hy], color='black')
            # path
            if r.path:
                px = [p[0] for p in r.path]
                py = [p[1] for p in r.path]
                self.ax.plot(px, py, 'b--', alpha=0.5)
                
        plt.pause(0.001)

import math
