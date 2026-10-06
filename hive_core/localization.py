import random
import math
from hive_core.types import Pose2D
from hive_core.config import is_enabled

class MockLocalizer:
    def __init__(self):
        self.drift_rate = 0.05  # 5cm drift per meter
        self.accumulated_dist = 0.0
        self.last_pose = None
        self.wrong_aisle_jumps = 0

    def process_odometry(self, true_pose: Pose2D, odom_pose: Pose2D, map_context: str) -> Pose2D:
        # Simulate odometry drift
        if self.last_pose:
            dist = math.hypot(true_pose.x - self.last_pose.x, true_pose.y - self.last_pose.y)
            self.accumulated_dist += dist
        self.last_pose = Pose2D(true_pose.x, true_pose.y, true_pose.theta)
        
        drift_x = odom_pose.x + (self.accumulated_dist * self.drift_rate)
        drift_y = odom_pose.y + (self.accumulated_dist * self.drift_rate)
        
        corrected_pose = Pose2D(drift_x, drift_y, odom_pose.theta)
        
        # S3: Odometry drift recovery (scan matching)
        if is_enabled('landmarks'):  # Using landmarks/scan matching to represent correction
            # Correct the drift by 95%
            corrected_pose.x = true_pose.x + (drift_x - true_pose.x) * 0.05
            corrected_pose.y = true_pose.y + (drift_y - true_pose.y) * 0.05
            self.accumulated_dist *= 0.05 # Reset drift
            
        # S4: Identical aisles
        if map_context == "identical_aisles":
            if not is_enabled('loc_confidence_gate'):
                # Baseline: blindly trust best match even if ratio test fails -> jump to wrong aisle
                if random.random() < 0.3: # 30% chance to jump
                    corrected_pose.x += 10.0 # Jump 10m to next aisle
                    self.wrong_aisle_jumps += 1
            else:
                # Hivemind: Multi-hypothesis ratio test rejects ambiguous matches
                pass # Stays in correct aisle
                
        # S5: Wrong loop closure
        if map_context == "wrong_loop":
            if not is_enabled('map_write_gate'):
                # Baseline: applies wrong loop closure -> warp
                corrected_pose.covariance = 999.0 # Warped
            else:
                # Hivemind: geometric verification fails, rollback
                corrected_pose.covariance = 0.01

        return corrected_pose
