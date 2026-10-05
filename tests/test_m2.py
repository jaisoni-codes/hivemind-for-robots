import sys
import os
sys.path.append(os.path.abspath('.'))

import time
from hive_core.memory import LivingMemory
from hive_core.types import Detection, Pose2D

def test_m2_living_memory():
    mem = LivingMemory()
    
    # 1. Detection creates a record
    d1 = Detection(label='toolbox', range=2.0, bearing=0.0, confidence=0.8, x=5.0, y=5.0, timestamp=time.time())
    mem.ingest_detection(d1, 'robot_1')
    
    records = mem.get_all()
    assert len(records) == 1
    assert records[0].state == 'ACTIVE'
    
    # 2. Negative observation (robot looks at 5.0, 5.0 and sees nothing)
    mem.process_negative_observation(Pose2D(3.0, 5.0, 0.0), fov_range=3.0, fov_angle=1.57, timestamp=time.time())
    mem.process_negative_observation(Pose2D(3.0, 5.0, 0.0), fov_range=3.0, fov_angle=1.57, timestamp=time.time())
    mem.process_negative_observation(Pose2D(3.0, 5.0, 0.0), fov_range=3.0, fov_angle=1.57, timestamp=time.time())
    mem.process_negative_observation(Pose2D(3.0, 5.0, 0.0), fov_range=3.0, fov_angle=1.57, timestamp=time.time())
    
    records = mem.get_all()
    assert records[0].state == 'GONE', f"State is {records[0].state}, expected GONE"
    
    # 3. Decay -> STALE
    # 900 seconds is 3 half lives -> confidence drops to 0.9 * 0.125 = 0.11 < 0.3
    d2 = Detection(label='ladder', range=2.0, bearing=0.0, confidence=0.9, x=1.0, y=1.0, timestamp=time.time() - 900)
    mem.ingest_detection(d2, 'robot_2')
    mem.update_decay(current_time=time.time())
    records = mem.get_all()
    ladder_rec = [r for r in records if r.label == 'ladder'][0]
    assert ladder_rec.state == 'STALE', f"Expected STALE, got {ladder_rec.state}"

    # 4. Persistence
    mem.persist()
