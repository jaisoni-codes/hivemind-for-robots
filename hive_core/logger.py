import json
import os
import time

class BlackBoxLogger:
    def __init__(self, log_dir="logs"):
        os.makedirs(log_dir, exist_ok=True)
        self.log_dir = log_dir
        self.file_index = 0
        self.log_file = os.path.join(self.log_dir, f"blackbox_{int(time.time())}_{self.file_index}.jsonl")
        self.max_lines = 50000
        self.line_count = 0
        
    def log_event(self, event_type: str, reason_code: str, data: dict):
        if self.line_count >= self.max_lines:
            self.file_index += 1
            self.log_file = os.path.join(self.log_dir, f"blackbox_{int(time.time())}_{self.file_index}.jsonl")
            self.line_count = 0
            
        entry = {
            "time": time.time(),
            "type": event_type,
            "reason": reason_code,
            "data": data
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self.line_count += 1
