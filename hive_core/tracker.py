import math
import numpy as np
import pickle
import os
from typing import List, Dict, Tuple
from hive_core.config import is_enabled

class DynamicTrack:
    def __init__(self, track_id: str, x: float, y: float, timestamp: float):
        self.id = track_id
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.last_update = timestamp
        self.alpha = 0.6
        self.beta = 0.4
        self.active = True
        
        # History of past 4 steps (at ~0.5s intervals) for MLP predictor
        self.history = [[x, y]] * 4
        self.history_times = [timestamp] * 4

    def update(self, x: float, y: float, timestamp: float):
        dt = timestamp - self.last_update
        if dt <= 0:
            return
            
        residual_x = x - (self.x + self.vx * dt)
        residual_y = y - (self.y + self.vy * dt)
        
        self.x += self.vx * dt + self.alpha * residual_x
        self.y += self.vy * dt + self.alpha * residual_y
        self.vx += (self.beta / dt) * residual_x
        self.vy += (self.beta / dt) * residual_y
        self.last_update = timestamp
        
        # Update history
        self.history.append([self.x, self.y])
        self.history_times.append(timestamp)
        if len(self.history) > 4:
            self.history.pop(0)
            self.history_times.pop(0)

class Tracker:
    def __init__(self):
        self.tracks: Dict[str, DynamicTrack] = {}
        self.association_radius = 1.0
        self.model = None
        if os.path.exists('hive_ml/predictor.pkl'):
            with open('hive_ml/predictor.pkl', 'rb') as f:
                self.model = pickle.load(f)
        
    def process_detections(self, detections: List[Tuple[float, float]], timestamp: float):
        unassigned_detections = list(detections)
        for track_id, track in list(self.tracks.items()):
            if not track.active:
                continue
            dt = timestamp - track.last_update
            if dt > 1.0:
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
                track.active = False
                
        for d in unassigned_detections:
            new_id = f"trk_{int(timestamp*1000)}_{len(self.tracks)}"
            self.tracks[new_id] = DynamicTrack(new_id, d[0], d[1], timestamp)
            
    def get_predictions(self, horizon_s: float = 3.0, steps: int = 6) -> Dict[str, List[Tuple[float, float]]]:
        preds = {}
        use_mlp = is_enabled('prediction') and self.model is not None
        
        for t_id, track in self.tracks.items():
            if not track.active:
                continue
                
            track_preds = []
            if use_mlp:
                try:
                    # Format history relative to latest point
                    hist = np.array(track.history)
                    origin = hist[-1].copy()
                    hist_rel = (hist - origin).flatten()
                    
                    # Predict 6 steps
                    future_rel = self.model.predict([hist_rel])[0]
                    future_rel = future_rel.reshape(steps, 2)
                    for px, py in future_rel:
                        track_preds.append((float(origin[0] + px), float(origin[1] + py)))
                except Exception:
                    use_mlp = False # Fallback
            
            if not use_mlp:
                dt = horizon_s / steps
                for i in range(1, steps + 1):
                    track_preds.append((track.x + track.vx * (i * dt), track.y + track.vy * (i * dt)))
            
            preds[t_id] = track_preds
            
        return preds
