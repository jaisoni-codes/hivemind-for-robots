import sys
import os
sys.path.append(os.path.abspath('.'))
import time
from hive_core.memory import LivingMemory
from hive_core.types import Detection, Pose2D
from hive_core.config import Config

def test_a1_write_gate_hivemind():
    # HIVEMIND mode: loc_confidence_gate is ON
    Config.load('hivemind')
    mem = LivingMemory()
    
    det = Detection(label='toolbox', range=2.0, bearing=0.0, confidence=0.8, x=5.0, y=5.0)
    # Robot is DEGRADED, should be ignored
    mem.ingest_detection(det, 'r1', loc_state='DEGRADED')
    
    assert len(mem.get_all()) == 0, "Degraded robot wrote to memory despite write gate!"

    # Robot is OK, should be accepted
    mem.ingest_detection(det, 'r1', loc_state='OK')
    assert len(mem.get_all()) == 1, "OK robot failed to write to memory!"

def test_a1_write_gate_baseline():
    # BASELINE mode: loc_confidence_gate is OFF
    Config.load('baseline')
    mem = LivingMemory()
    
    det = Detection(label='toolbox', range=2.0, bearing=0.0, confidence=0.8, x=5.0, y=5.0)
    # Robot is DEGRADED, but gate is OFF so it should write
    mem.ingest_detection(det, 'r1', loc_state='DEGRADED')
    
    assert len(mem.get_all()) == 1, "Baseline mode failed to write degraded data!"
