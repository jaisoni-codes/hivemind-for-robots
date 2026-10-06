# V1 Audit
- M0 (Setup): DONE (pytest tests/test_skeleton.py)
- M1 (FastSim, grid): DONE (pytest tests/test_m1.py)
- M2 (Memory): DONE (pytest tests/test_m2.py)
- M3 (Brain): DONE (pytest tests/test_m3.py)
- M4 (Tracker/Shield): DONE (pytest tests/test_m4.py)
- M5-M7 (Gazebo): PARTIAL (Adapter skeleton created, Gazebo setup skipped due to local Windows env limitations)
- M8 (Chatbot): DONE (python scenarios/chat_demo.py)
- M9 (Scale/Bench): DONE (python hive_bench/benchmark.py)
- M10 (RL): MISSING (WOW priority)
- M11 (Open-vocab): MISSING (WOW priority)
- M12 (Videos/Docs): PARTIAL (README written, videos pending)

## Smallest Refactors for v2
- Add boolean flags to toggle baseline vs hivemind mode (created in configs/).
- Add confidence check to map/memory writing logic (loc_confidence_gate).
- Split dummy simulator detections into Oracle vs 'Camera/Trained' detector.


## V2.1 Live Mode Audit
- A2 (Scenario harness): DONE
- A5 (Trained detector): DONE
- Dashboard/Scenario Lab: DONE (static HTML, migrating to dynamic web app for Live mode)
- World-mutation hook: MISSING (FastSim currently static after init)

Scheduled: L0 -> L5.
