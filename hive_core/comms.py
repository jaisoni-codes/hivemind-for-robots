import time
from typing import List, Dict, Optional
from hive_core.types import Detection, Task, RobotStatus
from hive_core.config import is_enabled

class CommsNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.state = "CONNECTED" # CONNECTED, DEGRADED, DISCONNECTED, SAFE
        self.tx_buffer_detections: List[Detection] = []
        self.rx_buffer_tasks: List[Task] = []
        self.seq_counter = 0
        self.last_sync = time.time()
        
    def set_state(self, new_state: str):
        self.state = new_state
        
    def send_detection(self, det: Detection) -> Optional[Detection]:
        self.seq_counter += 1
        det.seq_num = self.seq_counter
        
        if not is_enabled('comms_autonomy') or self.state == "CONNECTED":
            return det
        else:
            # Buffer if disconnected or degraded
            self.tx_buffer_detections.append(det)
            return None
            
    def sync_tx(self) -> List[Detection]:
        if self.state == "CONNECTED":
            flushed = self.tx_buffer_detections.copy()
            self.tx_buffer_detections.clear()
            return flushed
        return []

    def receive_task(self, task: Task) -> bool:
        if not is_enabled('comms_autonomy'):
            return True
            
        current_time = time.time()
        age = current_time - task.timestamp
        
        # A6: TTL check. Never execute a motion command older than TTL
        if age > task.ttl:
            # Drop stale command to prevent safety issues (latency handling)
            return False
            
        self.rx_buffer_tasks.append(task)
        return True
