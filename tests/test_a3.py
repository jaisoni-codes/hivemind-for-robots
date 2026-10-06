import sys
import os
sys.path.append(os.path.abspath('.'))
from hive_core.config import Config
from hive_core.tracker import Tracker
from hive_core.shield import SafetyShield
from hive_core.types import Pose2D

def test_a3_ml_predictor():
    Config.load('hivemind')
    tracker = Tracker()
    assert tracker.model is not None, "Trained ML model not loaded!"
    
    # Process some detections to build history
    for i in range(5):
        tracker.process_detections([(1.0 + i*0.5, 2.0 + i*0.5)], i * 0.5)
        
    preds = tracker.get_predictions()
    assert len(preds) == 1
    
    # Since config is hivemind and model is loaded, it should have used the MLP
    track_id = list(preds.keys())[0]
    assert len(preds[track_id]) == 6, "Should predict 6 future steps"
    
def test_a3_occlusion_cap():
    Config.load('hivemind') # occlusion_risk is ON
    shield = SafetyShield(max_v=1.0)
    
    # With target_v = 1.0 (full speed), the shield should cap it to 0.5
    v, w = shield.compute_safe_velocity(Pose2D(0,0,0), target_v=1.0, target_w=0.0, dynamic_predictions={}, other_robots=[])
    assert v <= 0.5, f"Occlusion risk cap failed, speed is {v}"

    Config.load('baseline') # occlusion_risk is OFF
    shield_base = SafetyShield(max_v=1.0)
    v2, w2 = shield_base.compute_safe_velocity(Pose2D(0,0,0), target_v=1.0, target_w=0.0, dynamic_predictions={}, other_robots=[])
    assert v2 > 0.5, f"Baseline should not be capped, speed is {v2}"
