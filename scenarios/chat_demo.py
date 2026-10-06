import sys
import os
sys.path.append(os.path.abspath('.'))
import time
import math
from hive_chat.parser import FallbackParser
from hive_core.memory import LivingMemory
from hive_core.types import Detection, Pose2D

def run_chat_demo():
    print("=== HIVEMIND Chat Interface (v2) ===")
    mem = LivingMemory()
    mem.ingest_detection(Detection('fire extinguisher', 1.0, 0.0, 0.9, x=8.5, y=2.0, timestamp=time.time() - 300), 'robot_1')
    mem.ingest_detection(Detection('toolbox', 1.0, 0.0, 0.8, x=1.0, y=5.0, timestamp=time.time()), 'robot_2')
    
    parser = FallbackParser()
    
    # Mock robots
    robot_poses = {
        'robot_1': Pose2D(0, 0, 0),
        'robot_2': Pose2D(10, 10, 0)
    }
    
    while True:
        try:
            cmd = input("\nUser: ")
        except EOFError:
            break
        if cmd.lower() in ['exit', 'quit']:
            break
            
        parsed = parser.parse(cmd)
        if "error" in parsed:
            print(f"System: {parsed['error']}")
            continue
            
        action = parsed['action']
        label = parsed['label']
        
        records = [r for r in mem.get_all() if r.label == label]
        
        if not records:
            print(f"System: I have no memory of a '{label}' in the building.")
            continue
            
        target = records[0]
        
        # A6: Show nearest-by-distance and best-by-travel-time
        # Mock calculation
        dists = []
        for r_id, pose in robot_poses.items():
            dist = math.hypot(target.pose.x - pose.x, target.pose.y - pose.y)
            # Mock ETA: distance / speed + turn penalty
            eta = dist / 1.0 + (2.0 if r_id == 'robot_1' else 0.0) 
            dists.append({'id': r_id, 'dist': dist, 'eta': eta})
            
        dists.sort(key=lambda x: x['dist'])
        nearest_dist = dists[0]
        
        dists.sort(key=lambda x: x['eta'])
        best_eta = dists[0]
        
        if action == "find":
            print(f"System: Nearest by straight-line distance is {nearest_dist['id']} ({nearest_dist['dist']:.1f} m).")
            print(f"System: Chosen target by travel time is {best_eta['id']} (ETA {best_eta['eta']:.1f} s).")
            # Exact message required by PS
            print(f"System: I have assigned the task to {best_eta['id']}")
            
            # Simulate arrival
            time.sleep(1) 
            # Exact message required by PS
            print(f"System: {best_eta['id'].capitalize()} has reached the {label} successfully.")
            
        elif action == "last_seen":
            age = int(time.time() - target.last_seen)
            print(f"System: '{label}' was last seen {age} seconds ago at ({target.pose.x:.1f}, {target.pose.y:.1f}).")

if __name__ == '__main__':
    run_chat_demo()
