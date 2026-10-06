import os

scenarios = [
    (1, 'unknown_start', 'T1', 'No goal without a map', 'SLAM + frontier exploration', '% area mapped vs time'),
    (2, 'curiosity_vs_routine', 'T2', 'Map never improves', 'Curiosity patrols of stale zones', 'Map freshness'),
    (3, 'odometry_drift', 'T1', 'Pose error grows', 'Scan-to-map matching + loop closure', 'Pose error per metre'),
    (4, 'identical_aisles', 'T1', 'Robot believes it is in another aisle', 'Multi-hypothesis pose, ratio test', 'Wrong-aisle rate'),
    (5, 'wrong_loop_closure', 'T3', 'Map warps', 'Geometric verification + map rollback', 'Map consistency'),
    (6, 'narrow_corridor', 'T1', 'Clips walls', 'Footprint-aware inflated costmap', 'Collisions'),
    (7, 'gap_looks_open', 'T2', 'Gets stuck', 'Configuration-space planning', 'Stuck rate'),
    (8, 'pallet_appears', 'T1', 'Collides with stale map', 'Local map update + replan', 'Detection-to-replan latency'),
    (9, 'dead_end', 'T2', 'Repeats attempts', 'No-progress detect, edge BLOCKED', 'Retries'),
    (10, 'temporary_restricted_zone', 'T3', 'Enters zone', 'BLOCKED state with decay + VERIFY', 'Zone violations'),
    (11, 'layout_changes', 'T3', 'Old map invalid', 'Change detection + map update', 'Map IoU after change'),
    (12, 'human_blocks_robot', 'T3', 'Oscillates', 'Wait then detour policy', 'Oscillation count'),
    (13, 'object_moved', 'T1', 'DB points to old spot', 'Negative observation -> MOVED -> search', 'Relocation accuracy'),
    (14, 'stale_memory', 'T2', 'Blind trip', 'VERIFY task first', 'Wasted trips'),
    (15, 'several_extinguishers', 'T2', 'Euclid-nearest is behind a wall', 'Pair choice by path ETA', 'Task time vs distance rule'),
    (16, 'world_keeps_changing', 'T2', 'One-time map decays', 'Living memory with decay', 'Memory accuracy over time'),
    (17, 'sudden_human', 'T1', 'No prediction', 'Tracker + trained predictor', 'Collisions, near-misses'),
    (18, 'human_turns_suddenly', 'T2', 'Wrong prediction', 'Uncertainty-aware margin', 'Near-misses'),
    (19, 'forklift', 'T1', 'Margin too small', 'Class-specific margin + swept area', 'Collisions'),
    (20, 'several_humans', 'T2', 'Local minimum', 'Multi-agent prediction, wait/retreat', 'Success rate'),
    (21, 'blind_corner', 'T3', 'Late reaction', 'Occlusion-aware speed cap', 'Near-misses'),
    (22, 'human_crosses_path', 'T2', 'Late braking', 'Arrival-time-aware risk', 'Min time-to-collision'),
    (23, 'unseen_not_absent', 'T3', 'Treats unseen as free', 'Unknown-space risk layer', 'Collisions at occluded crossing'),
    (24, 'glass_shiny_surface', 'T3', 'Misses obstacle', 'Confidence + multi-frame', 'Collisions'),
    (25, 'lighting_change', 'T3', 'Camera fails', 'LiDAR-first navigation', 'Nav success in dark zone'),
    (26, 'dust_sensor_noise', 'T3', 'Ghost obstacles', 'Filtering + confidence-aware speed', 'False-stop rate'),
    (27, 'brain_link_lost', 'T1', 'Robot helpless', 'Autonomy modes, local goal, shield', 'Safe-stop rate'),
    (28, 'robot_dies', 'T1', 'Task stuck', 'Heartbeat + reassignment', 'Recovery time'),
    (29, 'two_robots_one_corridor', 'T1', 'Deadlock', 'Reservation, priority, pull-over bay', 'Deadlocks per 100 runs'),
    (30, 'traffic_jam', 'T2', 'Queue on shortest path', 'Learned ETA + congestion-aware assignment', 'Throughput'),
    (31, 'battery_low', 'T4', 'Dies mid-task', 'Battery-aware allocation + dock', 'Tasks lost'),
    (32, 'wifi_dead_zone', 'T3', 'Stale commands', 'Buffering, command TTL, degraded mode', 'Task completion'),
    (33, 'swarm_grows_4_to_64', 'T1', 'Compute blow-up', 'Zones + decentralised avoidance', 'Compute vs N'),
    (34, 'brain_overload', 'T2', 'Central bottleneck', 'Hierarchical split', 'Brain ms per cycle'),
    (35, 'command_latency_500ms', 'T2', 'Acts on stale command', 'Robot-side safety decisions', 'Collisions under lag')
]

os.makedirs('scenarios/yaml', exist_ok=True)
for num, name, tier, fail_by, mech, metric in scenarios:
    filepath = f"scenarios/yaml/s{num:02d}_{name}.yaml"
    with open(filepath, 'w') as f:
        f.write(f"id: {num}\n")
        f.write(f"name: '{name}'\n")
        f.write(f"tier: '{tier}'\n")
        f.write(f"baseline_fails_by: '{fail_by}'\n")
        f.write(f"hivemind_mechanism: '{mech}'\n")
        f.write(f"metric: '{metric}'\n")
        f.write("seed: 42\n")

print("Created 35 YAML files.")
