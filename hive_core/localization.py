import random
import math
from typing import List, Tuple
from hive_core.types import Pose2D, Detection, ObjectRecord
from hive_core.config import is_enabled

class MockLocalizer:
    def __init__(self):
        self.drift_rate = 0.05
        self.accumulated_dist = 0.0
        self.last_pose = None
        self.wrong_aisle_jumps = 0

    def process_odometry(self, true_pose: Pose2D, odom_pose: Pose2D, map_context: str) -> Pose2D:
        if self.last_pose:
            dist = math.hypot(true_pose.x - self.last_pose.x, true_pose.y - self.last_pose.y)
            self.accumulated_dist += dist
        self.last_pose = Pose2D(true_pose.x, true_pose.y, true_pose.theta)
        
        drift_x = odom_pose.x + (self.accumulated_dist * self.drift_rate)
        drift_y = odom_pose.y + (self.accumulated_dist * self.drift_rate)
        
        corrected_pose = Pose2D(drift_x, drift_y, odom_pose.theta)
        
        if is_enabled('landmarks'):
            corrected_pose.x = true_pose.x + (drift_x - true_pose.x) * 0.05
            corrected_pose.y = true_pose.y + (drift_y - true_pose.y) * 0.05
            self.accumulated_dist *= 0.05 
            
        if map_context == "identical_aisles":
            if not is_enabled('loc_confidence_gate'):
                if random.random() < 0.3:
                    corrected_pose.x += 10.0
                    self.wrong_aisle_jumps += 1
            else:
                pass 
                
        if map_context == "wrong_loop":
            if not is_enabled('map_write_gate'):
                corrected_pose.covariance = 999.0
            else:
                corrected_pose.covariance = 0.01

        return corrected_pose

    def relocalize(self, raw_detections: List[Detection], memory_landmarks: List[ObjectRecord]) -> Tuple[bool, Pose2D]:
        """
        A4: LOST recovery using natural landmarks.
        raw_detections: what the robot currently sees (local frame ranges/bearings, though Detection object 
                        currently has x/y, we'll assume range/bearing are valid).
        memory_landmarks: trusted stable objects from LivingMemory.
        """
        if not is_enabled('landmarks'):
            return False, Pose2D(0,0,0)
            
        # Simplified Mock: If the robot sees an object that matches a memory landmark by label,
        # we can calculate the robot's global pose using trigonometry.
        matches = []
        for det in raw_detections:
            for lm in memory_landmarks:
                if det.label == lm.label:
                    # In a real system, we'd do a ratio test or least squares on multiple landmarks.
                    # Here we just use the first strong match for demonstration.
                    
                    # Robot global pos:
                    # rx + range * cos(rtheta + bearing) = lx
                    # ry + range * sin(rtheta + bearing) = ly
                    # Assuming theta is known/compass for simplicity:
                    rtheta = 0.0 # Mock compass
                    rx = lm.pose.x - det.range * math.cos(rtheta + det.bearing)
                    ry = lm.pose.y - det.range * math.sin(rtheta + det.bearing)
                    
                    return True, Pose2D(rx, ry, rtheta)
                    
        return False, Pose2D(0,0,0)

