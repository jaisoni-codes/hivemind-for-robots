# HIVEMIND: Centralized Intelligence for Dynamic Swarm Navigation

An advanced, marker-free, GPS-free multi-robot navigation system with shared memory, dynamic obstacle avoidance, task ranking, and an LLM chatbot interface. 

This repository fulfills the complete requirements of the **Bharat Forge Problem Statement (V1, V2, and V2.1 Addendum)**.

## Quick Start (3 Commands)

1. **Install dependencies:**
   `ash
   pip install -r requirements.txt
   `
2. **Run the Live Interactive Demo (Operator Console):**
   `ash
   python app.py
   `
   *Then open http://localhost:5000 in your browser to drop obstacles and test the swarm live!*
3. **Run the Scenario Lab (35 Failure Modes Report):**
   `ash
   make lab
   `
   *(On Windows without make, run python scripts/make_lab.py and open scenario_lab.html)*

## Core Architecture

- **hive_core**: A pure Python, ROS-agnostic brain implementing A* grid routing, ETA-based task allocation (Hungarian algorithm), and a Safety Shield. 
- **Living Memory**: Objects have temporal decay. "Unseen" changes are correctly ignored by the robots until physically discovered via lidar/camera, preventing ground-truth leakage.
- **Trained Trajectory Predictor**: Uses an MLP to predict human/forklift movement, reducing ADE (Average Displacement Error) by ~38% compared to standard Kalman filters.
- **Natural Landmarks**: Automatically promotes static objects to landmarks for kidnaped-robot relocalisation without artificial QR codes.
- **Comms Autonomy**: Handles disconnected robots via local buffering and command TTLs to prevent acting on stale data.

## Addendum Features Included
- **Scenario Harness (A2/A7)**: Automated pipeline testing 35 real failure scenarios, generating a static HTML Scenario Lab.
- **Live Interactive Mode (L0-L5)**: A Flask-based operator console allowing judges to spawn dynamic agents (humans, forklifts) and semantic objects in real-time. Features TRUTH vs BELIEF layer toggles.
- **Advanced Chat (L2)**: Explains 'why' tasks were allocated based on battery-aware travel time vs straight-line distance.

## Hardware & Fallback Note
Due to the constraints of the host hardware (Windows 11, Integrated GPU, 12GB RAM), heavy Gazebo 3D rendering is bypassed using our custom, high-speed mathematical simulator (**FastSim**). The logic in hive_core remains identically structured for ROS 2 deployment via the provided hive_ros adapters.
