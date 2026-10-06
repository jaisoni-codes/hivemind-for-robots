# PS Compliance Matrix

| PS requirement | Where implemented | Proof to attach |
|----------------|-------------------|-----------------|
| No GPS, no markers, no ground truth in the robot | Lidar scan matching, shared grid, dock frame, landmarks | No-ground-truth-leak test; V1 |
| Frequent, unpredictable changes | Tracker + trained predictor, Living Memory | Scenarios 8, 11, 13, 17-23; V3, V4 |
| Collaboratively plan optimal path, avoid collisions | Allocator, reservations, Safety Shield, zone graph | Scenarios 29, 30; collision table |
| Dynamic ranking of tasks by travel time | Allocator with path ETA + learned ETA | ETA error plot; ranking log |
| Memory persistence in a shared database | Living Memory (SQLite), multi-robot merge | Restart test; V3 |
| Same efficiency in new environment and larger swarm | Config-only WORLD-L, hierarchy, benchmarks 4-64 | V1, V2, scaling plots |
| Explore and map object locations automatically | Frontier explorer + curiosity + detector | Coverage curve; V1 |
| 'Design and train' with ML/DL/RL | Trained trajectory predictor, ETA model, detector | Training report, curves, metrics |
| ROS-compatible platform | ROS 2 + Gazebo | Launch files, V1-V4 from Gazebo |
| Environment at least 10x10 m | WORLD-S 12x12, WORLD-L 30x30+ | World files |
| At least 4 robots | 4 to 12 in Gazebo, 64 in FastSim | V2, benchmark |
| At least 10 unique objects | 14 classes in the world | World file, memory dump |
| At least 3 dynamic obstacles | 3 to 5 scripted dynamic agents | V4 |
| Deliverable: GitHub + README | Repo, 3-command install, make demo | Fresh-clone test |
| Deliverable: 4 simulation videos | V1, V2, V3, V4 | /videos |
| Deliverable: technical report, presentation | Section 9 specs | docs/ |
| Bonus: chatbot, assignment & arrival messages | Chat module | V5; GUI screenshot |
