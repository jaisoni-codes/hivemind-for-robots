import sys
import os
sys.path.append(os.path.abspath('.'))
from hive_core.config import Config
from hive_core.memory import LivingMemory
from hive_core.localization import MockLocalizer
from hive_core.types import Pose2D, Detection

def test_a4_kidnapped_robot():
    Config.load('hivemind')
    mem = LivingMemory()
    loc = MockLocalizer()
    
    # 1. Add a natural landmark to memory (e.g. fire extinguisher at x=10, y=10)
    # We simulate multiple detections so it gains high stability score
    for i in range(10):
        det = Detection(label='fire_extinguisher', range=2.0, bearing=0.0, confidence=0.9, x=10.0, y=10.0)
        mem.ingest_detection(det, 'r1', 'OK')
        
    landmarks = mem.get_landmarks()
    assert len(landmarks) == 1, "Failed to promote object to landmark"
    assert landmarks[0].label == 'fire_extinguisher'
    
    # 2. Kidnap the robot (it thinks it is at 0,0, but it's actually near the extinguisher)
    # Robot is physically at x=8, y=10, facing 0 rad.
    # It scans and sees the extinguisher at range 2.0, bearing 0.0
    raw_det = Detection(label='fire_extinguisher', range=2.0, bearing=0.0, confidence=0.9)
    
    # Baseline: no landmarks enabled
    Config.load('baseline')
    success_base, pose_base = loc.relocalize([raw_det], landmarks)
    assert not success_base, "Baseline should fail relocalisation"
    
    # Hivemind: landmarks enabled
    Config.load('hivemind')
    success_hive, pose_hive = loc.relocalize([raw_det], landmarks)
    assert success_hive, "Hivemind should succeed relocalisation"
    
    # It should recover x=8, y=10
    assert abs(pose_hive.x - 8.0) < 0.1, f"Expected x=8, got {pose_hive.x}"
    assert abs(pose_hive.y - 10.0) < 0.1, f"Expected y=10, got {pose_hive.y}"
