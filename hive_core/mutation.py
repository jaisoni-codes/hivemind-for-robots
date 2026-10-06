import json
import time
import os
from typing import Dict, Any

class WorldAdapter:
    def __init__(self, simulator):
        self.simulator = simulator
        self.log_file = "world_events.log"
        # Clear log on startup
        with open(self.log_file, "w") as f:
            f.write("")

    def mutate(self, op: Dict[str, Any]):
        """
        op format:
        {
            "op": "add" | "move" | "remove",
            "id": "w_0042",
            "class": "fire_extinguisher",
            "pose": [x, y, yaw],
            "size": [w, d, h],
            "speed": 0.8,
            "ts": time.time()
        }
        """
        op['ts'] = time.time()
        
        # Log ground truth mutation
        with open(self.log_file, "a") as f:
            f.write(json.dumps(op) + "\n")
            
        action = op.get('op')
        obj_id = op.get('id')
        
        if action == "add":
            self.simulator.add_dynamic_object(op)
        elif action == "move":
            self.simulator.move_dynamic_object(op)
        elif action == "remove":
            self.simulator.remove_dynamic_object(obj_id)
            
        return {"status": "success", "op": op}
