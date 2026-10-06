import sys
import os
sys.path.append(os.path.abspath('.'))
import time
from hive_core.config import Config
from hive_core.comms import CommsNode
from hive_core.types import Detection, Task, Pose2D

def test_a6_buffering():
    Config.load('hivemind') # comms_autonomy is ON
    node = CommsNode('r1')
    
    # Disconnect
    node.set_state('DISCONNECTED')
    det = Detection(label='toolbox', range=1.0, bearing=0.0, confidence=0.8)
    out = node.send_detection(det)
    assert out is None, "Should buffer, not return detection"
    assert len(node.tx_buffer_detections) == 1
    
    # Reconnect
    node.set_state('CONNECTED')
    flushed = node.sync_tx()
    assert len(flushed) == 1
    assert flushed[0].seq_num == 1
    assert len(node.tx_buffer_detections) == 0

def test_a6_ttl():
    Config.load('hivemind')
    node = CommsNode('r1')
    
    # Fresh task
    task = Task(id='t1', type='GOTO', priority=1, timestamp=time.time(), ttl=5.0)
    acc = node.receive_task(task)
    assert acc is True, "Fresh task should be accepted"
    
    # Stale task (e.g. latency > 5s)
    stale_task = Task(id='t2', type='GOTO', priority=1, timestamp=time.time() - 6.0, ttl=5.0)
    acc2 = node.receive_task(stale_task)
    assert acc2 is False, "Stale task should be rejected"
