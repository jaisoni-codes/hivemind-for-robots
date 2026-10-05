# Decisions Log

## M0: Setup and Environment
* **Platform:** FastSim-first approach selected.
* **Reasoning:** System is Windows 11 with 12 GB RAM, no dedicated GPU (Intel UHD Graphics), and 22 GB free disk space. No native ROS 2. Gazebo would be too heavy and requires WSL2/Docker which might struggle on this hardware. FastSim (pure Python) guarantees a working demo and faster iteration.
* **LLM:** Deferring cloud LLM usage for now; will rely on fallback parser / local mock until a key is provided.
