# HIVEMIND

Marker-free, memory-driven robot swarm for dynamic factories and warehouses.

## Core Architecture
Built on pure Python (`hive_core`), achieving swarm coordination, collision avoidance, and task allocation without relying on external infrastructure or markers.

## Features
- **Living Memory:** Shared memory that tracks and decays object confidences.
- **Dynamic Shield:** Predicts moving humans and perfectly avoids collisions.
- **Brain Allocation:** Smart ETA-based Hungarian assignment.
- **Hinglish Chatbot:** Query the swarm natively.

## Quickstart

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Live Demo:**
   ```bash
   python scenarios/runner.py
   ```

3. **Run Chatbot Demo:**
   ```bash
   python scenarios/chat_demo.py
   ```

4. **Run Benchmarks:**
   ```bash
   python hive_bench/benchmark.py
   ```

5. **Run Tests:**
   ```bash
   pytest tests/
   ```
