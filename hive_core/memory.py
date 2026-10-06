import sqlite3
import time
import math
from typing import List, Dict, Tuple, Optional
from hive_core.types import ObjectRecord, Pose2D, Detection, Event
from hive_core.config import is_enabled

class LivingMemory:
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        self.records: Dict[str, ObjectRecord] = {}
        self.half_life_sec = 300.0
        self.snapshots = {} # Map integrity snapshots
        
    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS objects (
                id TEXT PRIMARY KEY,
                label TEXT,
                x REAL,
                y REAL,
                confidence REAL,
                first_seen REAL,
                last_seen REAL,
                seen_count INTEGER,
                state TEXT,
                is_dynamic INTEGER
            )
        ''')
        self.conn.commit()

    def persist(self):
        cursor = self.conn.cursor()
        for r in self.records.values():
            cursor.execute('''
                INSERT OR REPLACE INTO objects 
                (id, label, x, y, confidence, first_seen, last_seen, seen_count, state, is_dynamic)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (r.id, r.label, r.pose.x, r.pose.y, r.confidence, r.first_seen, r.last_seen, 
                  r.seen_count, r.state, int(r.is_dynamic)))
        self.conn.commit()

    def _generate_id(self, label: str) -> str:
        return f"{label}_{int(time.time()*1000)}_{len(self.records)}"

    def ingest_detection(self, detection: Detection, robot_id: str, loc_state: str = "OK"):
        # Write gate for degraded/lost robots
        if is_enabled('loc_confidence_gate') and loc_state != "OK":
            return # Ignore data from uncertain robots
            
        best_match = None
        min_dist = 0.7
        
        for r_id, record in self.records.items():
            if record.label == detection.label:
                d = math.hypot(record.pose.x - detection.x, record.pose.y - detection.y)
                if d < min_dist:
                    min_dist = d
                    best_match = r_id
                    
        if best_match:
            record = self.records[best_match]
            record.pose.x = detection.x
            record.pose.y = detection.y
            record.confidence = min(1.0, record.confidence + detection.confidence * 0.5)
            record.last_seen = detection.timestamp
            record.seen_count += 1
            if record.state in ['GONE', 'MOVED']:
                record.state = 'ACTIVE'
            elif record.confidence > 0.3 and record.state == 'STALE':
                record.state = 'ACTIVE'
            if robot_id not in record.observed_by:
                record.observed_by.append(robot_id)
        else:
            new_id = self._generate_id(detection.label)
            self.records[new_id] = ObjectRecord(
                id=new_id,
                label=detection.label,
                pose=Pose2D(detection.x, detection.y, 0.0),
                confidence=detection.confidence,
                first_seen=detection.timestamp,
                last_seen=detection.timestamp,
                seen_count=1,
                state='ACTIVE',
                history=[(Pose2D(detection.x, detection.y, 0.0), detection.timestamp)],
                observed_by=[robot_id],
                is_dynamic=False
            )

    def process_negative_observation(self, robot_pose: Pose2D, fov_range: float, fov_angle: float, timestamp: float, loc_state: str = "OK"):
        if is_enabled('loc_confidence_gate') and loc_state != "OK":
            return
            
        for r_id, record in self.records.items():
            if record.state in ['GONE', 'MOVED']:
                continue
            
            d = math.hypot(record.pose.x - robot_pose.x, record.pose.y - robot_pose.y)
            if d < fov_range:
                angle_to = math.atan2(record.pose.y - robot_pose.y, record.pose.x - robot_pose.x)
                angle_diff = abs((angle_to - robot_pose.theta + math.pi) % (2*math.pi) - math.pi)
                if angle_diff <= fov_angle / 2.0:
                    if is_enabled('negative_observation'):
                        record.confidence -= 0.2
                        if record.confidence <= 0.1:
                            record.state = 'GONE'

    def update_decay(self, current_time: float):
        if not is_enabled('confidence_decay'):
            return
            
        for r_id, record in self.records.items():
            if record.state in ['GONE', 'MOVED']:
                continue
            dt = current_time - record.last_seen
            record.confidence = record.confidence * math.exp(-math.log(2) * dt / self.half_life_sec)
            if record.confidence < 0.3 and record.state == 'ACTIVE':
                record.state = 'STALE'
                
    def get_all(self) -> List[ObjectRecord]:
        return list(self.records.values())

    def snapshot(self, timestamp: float):
        # Very simple mock of map integrity snapshots
        self.snapshots[timestamp] = {k: v.confidence for k, v in self.records.items()}
        
    def rollback(self, timestamp: float):
        if timestamp in self.snapshots:
            snap = self.snapshots[timestamp]
            for k, conf in snap.items():
                if k in self.records:
                    self.records[k].confidence = conf
