import sys
import os
sys.path.append(os.path.abspath('.'))

import math
from hive_core.localization import MockLocalizer
from hive_core.types import Pose2D
from hive_core.config import Config

def test_scenario_3_odometry_drift():
    # Baseline
    Config.load('baseline')
    loc_base = MockLocalizer()
    p = Pose2D(0, 0, 0)
    for _ in range(100): # move 100 meters
        p.x += 1.0
        out_base = loc_base.process_odometry(p, Pose2D(p.x, p.y, p.theta), "normal")
    drift_base = math.hypot(out_base.x - p.x, out_base.y - p.y)
    
    # Hivemind
    Config.load('hivemind')
    loc_hive = MockLocalizer()
    p2 = Pose2D(0, 0, 0)
    for _ in range(100):
        p2.x += 1.0
        out_hive = loc_hive.process_odometry(p2, Pose2D(p2.x, p2.y, p2.theta), "normal")
    drift_hive = math.hypot(out_hive.x - p2.x, out_hive.y - p2.y)
    
    assert drift_base > 1.0, f"Baseline drift too small: {drift_base}"
    assert drift_hive < 0.5, f"Hivemind drift too large: {drift_hive}"

def test_scenario_4_identical_aisles():
    # Baseline
    Config.load('baseline')
    loc_base = MockLocalizer()
    for _ in range(20):
        loc_base.process_odometry(Pose2D(0,0,0), Pose2D(0,0,0), "identical_aisles")
        
    # Hivemind
    Config.load('hivemind')
    loc_hive = MockLocalizer()
    for _ in range(20):
        loc_hive.process_odometry(Pose2D(0,0,0), Pose2D(0,0,0), "identical_aisles")
        
    assert loc_base.wrong_aisle_jumps > 0, "Baseline didn't make wrong jumps!"
    assert loc_hive.wrong_aisle_jumps == 0, "Hivemind made wrong jumps!"
    
def test_scenario_5_wrong_loop_closure():
    # Baseline
    Config.load('baseline')
    loc_base = MockLocalizer()
    out_base = loc_base.process_odometry(Pose2D(0,0,0), Pose2D(0,0,0), "wrong_loop")
    
    # Hivemind
    Config.load('hivemind')
    loc_hive = MockLocalizer()
    out_hive = loc_hive.process_odometry(Pose2D(0,0,0), Pose2D(0,0,0), "wrong_loop")
    
    assert out_base.covariance > 100.0, "Baseline didn't warp!"
    assert out_hive.covariance < 1.0, "Hivemind didn't rollback!"
