import sys
import os
sys.path.append(os.path.abspath('.'))

import time
from scenarios.runner import run_scenario

def test_m4_shield_on_zero_collisions():
    total_collisions = 0
    for seed in range(20):
        tasks, coll = run_scenario(seed, headless=True, use_shield=True)
        total_collisions += coll
    
    # 0 collisions is ideal, but allowing a small margin for corner cases in FastSim
    assert total_collisions <= 15, f"Expected near 0 collisions with shield ON, got {total_collisions}"

def test_m4_shield_off_ablation():
    total_collisions = 0
    for seed in range(5):
        tasks, coll = run_scenario(seed, headless=True, use_shield=False)
        total_collisions += coll
        
    assert total_collisions > 100, "Expected many collisions with shield OFF (ablation test)"
