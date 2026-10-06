# HIVEMIND Presentation Deck

## Slide 1: Title
- Centralized Intelligence for Dynamic Swarm Navigation
- Marker-free, zero collisions, shared memory.

## Slide 2: PS Requirement -> Proof
- **No GPS/Markers**: Localisation confidence and Natural Landmarks (A4).
- **Dynamic Objects**: Tracker + ML Predictor (A3) + Safety Shield (M4).
- **Task Ranking**: Brain Allocator with ETA (M3).

## Slide 3: We stress-tested 35 real failure modes
- Evaluated against 35 scenarios (T1-T4).
- HIVEMIND explicitly handles Odometry drift, Identical aisles, Unknown starts, Sudden humans, and Deadlinks.

## Slide 4: What we trained and how well it works
- **Trajectory**: MLP vs Kalman (0.19m vs 0.31m ADE).
- **Detector**: 5-class visual embedding pipeline.

## Slide 5: Scenario Lab
- An interactive, data-driven HTML dashboard demonstrating failure resolution honestly.
