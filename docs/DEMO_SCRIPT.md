# Suggested 5-minute live demo (Live Interactive Mode)

1. **Show the warehouse and swarm (30s)**
   - Open the Live Operator Console (python app.py).
   - Open the web interface in the browser.
   - Point out the TRUTH layer (orange) and BELIEF layer (blue). Currently, they match.

2. **Drop a pallet on a robot's path (45s)**
   - Using the Palette, click **Drop Pallet** directly in front of obot_1.
   - Watch the ground truth (TRUTH) update immediately.
   - Watch obot_1 detect it, the BELIEF layer update, and obot_1 execute a detour replan.

3. **Place a fire extinguisher in view, ask for nearest (60s)**
   - Click **Drop Extinguisher** near obot_2.
   - In the chat, type ind the nearest fire extinguisher.
   - Note the output: "I have assigned the task to robot 2". Wait for the message: "Robot 2 has reached the fire extinguisher successfully."

4. **Unseen change & SCAN_AREA (60s)**
   - Uncheck "Show BELIEF". Drop an extinguisher far away from any robot.
   - Run ind the nearest fire extinguisher. The system will intentionally pick the *old* one because the new one is not in Living Memory (no ground truth leak).
   - A badge will indicate '1 unseen change'.
   - Type scan aisle 3 (or check this spot).
   - A robot will patrol there, see the new object, and the BELIEF layer will update.

5. **Dynamic Agents (45s)**
   - Click **Drop Human**.
   - Watch the dynamic human agent walk across the grid. The robots will yield, stop, and avoid collisions seamlessly.

6. **Judge Mode (60s)**
   - Click **Judge Mode (Random)**.
   - This drops multiple random obstacles, objects, and agents at valid locations.
   - Show how the swarm gracefully handles the chaos without deadlocks or crashes.
