import os
import threading
import time
import math
import random
import heapq
from flask import Flask, request, jsonify, render_template_string
from hive_core.mutation import WorldAdapter
from hive_core.types import Pose2D

app = Flask(__name__)

# Basic A* Path Planning
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star_search(start, goal, obstacles, width=20, height=20, grid_size=1.0):
    start_g = (round(start[0]), round(start[1]))
    goal_g = (round(goal[0]), round(goal[1]))
    
    frontier = []
    heapq.heappush(frontier, (0, start_g))
    came_from = {}
    cost_so_far = {}
    came_from[start_g] = None
    cost_so_far[start_g] = 0
    
    # Expand obstacles with a safety margin
    blocked = set()
    for obs in obstacles:
        ox, oy = round(obs[0]), round(obs[1])
        blocked.add((ox, oy))
        blocked.add((ox+1, oy))
        blocked.add((ox-1, oy))
        blocked.add((ox, oy+1))
        blocked.add((ox, oy-1))

    while frontier:
        current = heapq.heappop(frontier)[1]
        
        if current == goal_g:
            break
            
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
            next_node = (current[0] + dx, current[1] + dy)
            if 0 <= next_node[0] <= width and 0 <= next_node[1] <= height:
                if next_node in blocked:
                    continue
                new_cost = cost_so_far[current] + (1.414 if dx != 0 and dy != 0 else 1.0)
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + heuristic(goal_g, next_node)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current
                    
    if goal_g not in came_from:
        return [] # No path
        
    current = goal_g
    path = []
    while current != start_g:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

class DynamicHuman:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.timer = 0
    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            angle = random.uniform(0, 2*math.pi)
            speed = 0.8
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.timer = random.uniform(2, 5)
        
        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt
        if 2 < nx < 18 and 2 < ny < 18:
            self.x = nx
            self.y = ny
        else:
            self.timer = 0 # Bounce

class IntelligentRobot:
    def __init__(self, r_id, x, y):
        self.id = r_id
        self.x = x
        self.y = y
        self.theta = 0
        self.v = 0
        self.w = 0
        self.path = []
        self.target = None
        self.memory_obstacles = [] # BELIEF
        self.state = 'IDLE'

    def replan(self):
        if not self.target: return
        self.path = a_star_search((self.x, self.y), self.target, self.memory_obstacles)

    def update(self, dt, all_robots, humans, truth_objects):
        # 1. Perception (Update memory if truth object is within 4 meters)
        memory_changed = False
        new_memory = []
        for obj in truth_objects:
            dist = math.hypot(obj['pose'][0] - self.x, obj['pose'][1] - self.y)
            if dist < 4.0: # Sensor range
                new_memory.append((obj['pose'][0], obj['pose'][1]))
        
        # Add humans to memory if visible
        for h in humans:
            if math.hypot(h.x - self.x, h.y - self.y) < 4.0:
                new_memory.append((h.x, h.y))

        # Check if memory changed significantly
        if len(new_memory) != len(self.memory_obstacles):
            self.memory_obstacles = new_memory
            self.replan()

        if self.target is None or (len(self.path) == 0 and math.hypot(self.target[0]-self.x, self.target[1]-self.y) < 1.0):
            self.target = (random.uniform(3, 17), random.uniform(3, 17))
            self.replan()
            self.state = 'MOVING'

        # 2. Safety Shield (Robot-to-Robot & Robot-to-Human collision avoidance)
        safe_to_move = True
        for other in all_robots:
            if other.id != self.id:
                if math.hypot(other.x - self.x, other.y - self.y) < 1.2:
                    # Yield to lower ID
                    if self.id > other.id:
                        safe_to_move = False
        for h in humans:
            if math.hypot(h.x - self.x, h.y - self.y) < 1.5:
                safe_to_move = False # Stop for human

        if not safe_to_move:
            self.v = 0
            self.w = 0
            self.state = 'YIELDING'
            return

        # 3. Path Following
        if self.path:
            next_pt = self.path[0]
            dx = next_pt[0] - self.x
            dy = next_pt[1] - self.y
            dist = math.hypot(dx, dy)
            
            if dist < 0.5:
                self.path.pop(0)
            else:
                target_theta = math.atan2(dy, dx)
                angle_diff = (target_theta - self.theta + math.pi) % (2 * math.pi) - math.pi
                
                self.w = max(-2.0, min(2.0, angle_diff * 3.0))
                if abs(angle_diff) < 0.5:
                    self.v = 1.2
                else:
                    self.v = 0.0
        else:
            self.v = 0
            self.w = 0

        # Kinematic update
        self.theta += self.w * dt
        self.theta = (self.theta + math.pi) % (2 * math.pi) - math.pi
        self.x += self.v * math.cos(self.theta) * dt
        self.y += self.v * math.sin(self.theta) * dt

class RealSimulator:
    def __init__(self):
        self.robots = [IntelligentRobot('AGV-1', 2, 2), IntelligentRobot('AGV-2', 18, 18)]
        self.humans = []
        self.objects = {}
        # Initial shelves
        for x in [6, 14]:
            for y in [5, 6, 7, 8, 12, 13, 14, 15]:
                self.objects[f"rack_{x}_{y}"] = {"class": "shelf", "pose": [x, y, 0]}

    def step(self, dt):
        truth_objs = list(self.objects.values())
        for h in self.humans:
            h.update(dt)
        for r in self.robots:
            r.update(dt, self.robots, self.humans, truth_objs)

sim = RealSimulator()

def sim_loop():
    last_time = time.time()
    while True:
        now = time.time()
        sim.step(now - last_time)
        last_time = now
        time.sleep(0.04)

threading.Thread(target=sim_loop, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HIVEMIND Digital Twin</title>
    <style>
        body { display: flex; font-family: 'Segoe UI', sans-serif; margin: 0; height: 100vh; background: #0b0f19; color: #fff; }
        #sidebar { width: 350px; background: #1e293b; padding: 20px; z-index: 10; box-shadow: 2px 0 10px rgba(0,0,0,0.5); }
        h2 { color: #38bdf8; margin: 0 0 20px 0; }
        .btn { padding: 10px; background: #38bdf8; border: none; border-radius: 4px; cursor: pointer; color: #000; font-weight: bold; margin-bottom: 10px; width: 100%;}
        #canvas-container { flex-grow: 1; display: flex; align-items: center; justify-content: center; background: #0b0f19; }
        canvas { background: #0f172a; border: 1px solid #333; border-radius: 8px; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
    </style>
</head>
<body>
    <div id="sidebar">
        <h2>HIVEMIND Operator Console</h2>
        <p>Drag items to the grid. Robots will sense them, update memory, and replan routes.</p>
        <div draggable="true" ondragstart="event.dataTransfer.setData('type', 'pallet')" style="padding: 10px; background: #334155; margin-bottom: 10px; cursor: grab;">🧱 Drop Pallet</div>
        <div draggable="true" ondragstart="event.dataTransfer.setData('type', 'human')" style="padding: 10px; background: #334155; margin-bottom: 10px; cursor: grab;">🚶 Drop Moving Human</div>
        <button class="btn" onclick="fetch('/reset')">Reset World</button>
        <hr>
        <div id="chat" style="height: 200px; overflow-y: auto; background: #000; padding: 10px; font-family: monospace; font-size: 12px;"></div>
    </div>
    <div id="canvas-container" ondrop="drop(event)" ondragover="event.preventDefault()">
        <canvas id="view" width="800" height="800"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('view');
        const ctx = canvas.getContext('2d');
        let state = { robots: [], objects: {}, humans: [] };
        
        async function drop(ev) {
            ev.preventDefault();
            const type = ev.dataTransfer.getData("type");
            const rect = canvas.getBoundingClientRect();
            const simX = (ev.clientX - rect.left) / rect.width * 20.0;
            const simY = (ev.clientY - rect.top) / rect.height * 20.0;
            await fetch('/mutate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({op: 'add', class: type, pose: [simX, simY, 0]})
            });
            document.getElementById('chat').innerHTML += <div>> Deployed \ at \, \</div>;
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const scale = canvas.width / 20.0;
            
            // Grid
            ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 1;
            for(let i=0; i<=20; i++) {
                ctx.beginPath(); ctx.moveTo(i*scale, 0); ctx.lineTo(i*scale, 800); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(0, i*scale); ctx.lineTo(800, i*scale); ctx.stroke();
            }

            // Truth Objects
            for (const id in state.objects) {
                const obj = state.objects[id];
                ctx.fillStyle = obj.class === 'shelf' ? '#475569' : '#d97706';
                ctx.fillRect((obj.pose[0]-0.5)*scale, (obj.pose[1]-0.5)*scale, scale, scale);
            }
            
            // Humans
            state.humans.forEach(h => {
                ctx.fillStyle = '#a855f7';
                ctx.beginPath(); ctx.arc(h.x*scale, h.y*scale, 0.4*scale, 0, Math.PI*2); ctx.fill();
            });

            // Robots
            state.robots.forEach(r => {
                // Path
                ctx.strokeStyle = '#38bdf8'; ctx.setLineDash([5, 5]); ctx.beginPath();
                ctx.moveTo(r.x*scale, r.y*scale);
                r.path.forEach(p => ctx.lineTo(p[0]*scale, p[1]*scale));
                ctx.stroke(); ctx.setLineDash([]);
                
                // Sensor ring
                ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
                ctx.beginPath(); ctx.arc(r.x*scale, r.y*scale, 4*scale, 0, Math.PI*2); ctx.stroke();

                // Body
                ctx.save(); ctx.translate(r.x*scale, r.y*scale); ctx.rotate(r.theta);
                ctx.fillStyle = r.state === 'YIELDING' ? '#f59e0b' : '#38bdf8';
                ctx.fillRect(-0.4*scale, -0.25*scale, 0.8*scale, 0.5*scale);
                ctx.fillStyle = '#fff'; ctx.fillRect(0.2*scale, -0.1*scale, 0.2*scale, 0.2*scale);
                ctx.restore();
            });
            requestAnimationFrame(draw);
        }
        
        setInterval(async () => {
            const res = await fetch('/state');
            state = await res.json();
        }, 50);
        draw();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/state')
def get_state():
    robots = [{'id': r.id, 'x': r.x, 'y': r.y, 'theta': r.theta, 'path': r.path, 'state': r.state} for r in sim.robots]
    humans = [{'x': h.x, 'y': h.y} for h in sim.humans]
    return jsonify({'robots': robots, 'objects': sim.objects, 'humans': humans})

@app.route('/mutate', methods=['POST'])
def mutate():
    data = request.json
    if data['class'] == 'human':
        sim.humans.append(DynamicHuman('h', data['pose'][0], data['pose'][1]))
    else:
        sim.objects[f"obj_{time.time()}"] = data
    return jsonify({'status': 'ok'})

@app.route('/reset')
def reset():
    sim.objects = {k: v for k, v in sim.objects.items() if v.get('class') == 'shelf'}
    sim.humans = []
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
