import sys
import os
sys.path.append(os.path.abspath('.'))
from hive_core.config import Config
from hive_fastsim.simulator import MockCameraDetector

def test_a5_detector_oracle():
    Config.load('baseline')
    cam = MockCameraDetector()
    label, conf = cam.detect('human')
    assert label == 'human'
    assert conf == 1.0, "Oracle should return 1.0 confidence"

def test_a5_detector_trained():
    Config.load('hivemind')
    cam = MockCameraDetector()
    assert cam.model is not None, "Model not loaded!"
    
    labels = []
    confs = []
    for _ in range(100):
        label, conf = cam.detect('human')
        labels.append(label)
        confs.append(conf)
        
    human_count = labels.count('human')
    assert human_count > 90, f"mAP proxy too low, got {human_count} correct"
