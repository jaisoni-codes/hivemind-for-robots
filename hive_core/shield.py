import math
import numpy as np
from typing import List, Tuple, Dict
from hive_core.types import Pose2D

class SafetyShield:
    def __init__(self, robot_radius=0.3, max_v=1.0, max_w=2.0):
        self.robot_radius = robot_radius
        self.max_v = max_v
        self.max_w = max_w
        self.dt = 0.5
        self.predict_time = 2.0  # 2s horizon
        self.safe_dist = 0.3

    def compute_safe_velocity(self, pose: Pose2D, target_v: float, target_w: float, 
                              dynamic_predictions: Dict[str, List[Tuple[float, float]]],
                              other_robots: List[Pose2D],
                              use_shield: bool = True) -> Tuple[float, float]:
        if not use_shield:
            return target_v, target_w

        best_v = 0.0
        best_w = 0.0
        min_cost = float('inf')

        v_samples = [target_v, target_v * 0.5, 0.0, -0.5, -1.0] 
        w_samples = [target_w, target_w + 1.0, target_w - 1.0, 0.0, 2.0, -2.0]

        for v in v_samples:
            for w in w_samples:
                cost = self._evaluate_trajectory(pose, v, w, target_v, target_w, dynamic_predictions, other_robots)
                if cost < min_cost:
                    min_cost = cost
                    best_v = v
                    best_w = w

        if min_cost == float('inf'):
            return 0.0, 0.0

        return best_v, best_w

    def _evaluate_trajectory(self, pose: Pose2D, v: float, w: float, 
                             target_v: float, target_w: float,
                             dynamic_predictions: Dict[str, List[Tuple[float, float]]],
                             other_robots: List[Pose2D]) -> float:
        cost = 0.0
        curr_x, curr_y, curr_theta = pose.x, pose.y, pose.theta
        steps = int(self.predict_time / self.dt)
        
        cost += abs(v - target_v) * 2.0
        cost += abs(w - target_w) * 0.5

        min_clearance = float('inf')

        for i in range(1, steps + 1):
            curr_theta += w * self.dt
            curr_x += v * math.cos(curr_theta) * self.dt
            curr_y += v * math.sin(curr_theta) * self.dt

            for trk_id, preds in dynamic_predictions.items():
                if i - 1 < len(preds):
                    px, py = preds[i - 1]
                    dist = math.hypot(curr_x - px, curr_y - py)
                    if dist < (self.robot_radius + 0.3 + self.safe_dist):
                        return float('inf')
                    min_clearance = min(min_clearance, dist)

            for or_pose in other_robots:
                dist = math.hypot(curr_x - or_pose.x, curr_y - or_pose.y)
                if dist < (self.robot_radius * 2 + self.safe_dist):
                    return float('inf')
                min_clearance = min(min_clearance, dist)

        if min_clearance < 1.0:
            cost += (1.0 / min_clearance) * 5.0

        return cost
