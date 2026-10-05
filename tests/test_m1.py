import sys
import os
sys.path.append(os.path.abspath('.'))

from scenarios.runner import run_scenario

def test_m1_acceptance():
    for seed in range(5):
        tasks, coll = run_scenario(seed, headless=True)
        assert tasks >= 20, f"Seed {seed}: Not enough tasks completed"
        assert coll == 0, f"Seed {seed}: Collisions occurred"
