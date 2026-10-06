import math
import numpy as np
from typing import List, Dict, Tuple
import time
from hive_core.types import Pose2D

class DynamicTrack:
    def __init__(self, track_id: str, x: float, y: float, timestamp: float):
        self.id = track_id
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.last_update = timestamp
        # Alpha-beta filter parameters (simple alternative to full Kalman for fastsim)
        self.alpha = 0.6
        self.beta = 0.4
        self.active = True

    def update(self, x: float, y: float, timestamp: float):
        dt = timestamp - self.last_update
        if dt <= 0:
            return
            
        # Predict
        pred_x = self.x + self.vx * dt
        pred_y = self.y + self.vy * dt
        
        # Update
        residual_x = x - pred_x
        residual_y = y - pred_y
        
        self.x = pred_x + self.alpha * residual_x
        self.y = pred_y + self.alpha * residual_y
        self.vx = self.vx + (self.beta / dt) * residual_x
        self.vy = self.vy + (self.beta / dt) * residual_y
        self.last_update = timestamp

    def predict_future(self, horizon_s: float, steps: int) -> List[Tuple[float, float]]:
        predictions = []
        dt = horizon_s / steps
        for i in range(1, steps + 1):
            predictions.append((self.x + self.vx * (i * dt), self.y + self.vy * (i * dt)))
        return predictions

class Tracker:
    def __init__(self):
        self.tracks: Dict[str, DynamicTrack] = {}
        self.association_radius = 1.0
        
    def process_detections(self, detections: List[Tuple[float, float]], timestamp: float):
        unassigned_detections = list(detections)
        
        # Associate
        for track_id, track in list(self.tracks.items()):
            if not track.active:
                continue
                
            # Predict to current time
            dt = timestamp - track.last_update
            if dt > 1.0: # Lost track
                track.active = False
                continue
                
            pred_x = track.x + track.vx * dt
            pred_y = track.y + track.vy * dt
            
            best_det = None
            best_dist = self.association_radius
            
            for d in unassigned_detections:
                dist = math.hypot(d[0] - pred_x, d[1] - pred_y)
                if dist < best_dist:
                    best_dist = dist
                    best_det = d
                    
            if best_det:
                track.update(best_det[0], best_det[1], timestamp)
                unassigned_detections.remove(best_det)
            else:
                track.active = False # Mark inactive if no detection
                
        # Create new tracks
        for d in unassigned_detections:
            new_id = f"trk_{int(timestamp*1000)}_{len(self.tracks)}"
            self.tracks[new_id] = DynamicTrack(new_id, d[0], d[1], timestamp)
            
    def get_predictions(self, horizon_s: float = 3.0, steps: int = 6) -> Dict[str, List[Tuple[float, float]]]:
        preds = {}
        for t_id, track in self.tracks.items():
            if track.active:
                preds[t_id] = track.predict_future(horizon_s, steps)
        return preds
