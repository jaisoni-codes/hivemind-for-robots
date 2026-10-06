import sys
import os
sys.path.append(os.path.abspath('.'))

from scenarios.runner import run_scenario

def test_m1_acceptance():
    for seed in range(5):
        tasks, coll, duration = run_scenario(seed, headless=True)
        assert tasks >= 10, f"Seed {seed}: Not enough tasks completed"
        assert coll <= 10, f"Seed {seed}: Too many collisions"
