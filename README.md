# HIVEMIND for Robots
**Digital Twin & Fleet Dashboard for Swarm Intelligence**

This repository contains the pure Python + Flask implementation of the HIVEMIND Fleet Management system. It simulates a digital twin environment for autonomous AGVs operating within a warehouse setting, utilizing A* pathfinding, holonomic kinematics, and real-time operator dispatching.

## Features
- **Swarm Intelligence:** Multiple AGVs share a centralized "Living Memory" to track dynamic obstacles (pallets, extinguishers, moving humans).
- **Precision Dispatching:** Operators can view the exact belief state of the swarm and assign tasks to specific objects via the dashboard.
- **Holonomic Navigation:** Smooth point-mass kinematic movement ensures robots glide smoothly around obstacles without differential-drive turning radius issues (wiggling/orbiting).
- **A* Path Planning:** Real-time routing through grid-based aisles and dynamic obstacles.

## How to Run
1. Ensure you have Python installed.
2. Run `pip install flask`
3. Execute the latest iteration (e.g., `task_app_v8.py`):
   ```bash
   python task_app_v8.py
   ```
4. Open your browser to `http://127.0.0.1:5019` (port may vary based on iteration).
