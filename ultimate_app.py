import os
import threading
import time
import math
import random
import heapq
from flask import Flask, request, jsonify, render_template_string
from hive_core.mutation import WorldAdapter

app = Flask(__name__)

# Basic A* Path Planning
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star_search(start, goal, obstacles, width=20, height=20):
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
                if math.hypot(other.x - self.x, other.y - self.y) < 1.5:
                    if self.id > other.id:
                        safe_to_move = False
        for h in humans:
            if math.hypot(h.x - self.x, h.y - self.y) < 1.8:
                safe_to_move = False # Stop for human

        if not safe_to_move:
            self.v = 0
            self.w = 0
            self.state = 'YIELDING'
            return
        
        self.state = 'MOVING'

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
        self.robots = [IntelligentRobot('AGV-1', 2, 2), IntelligentRobot('AGV-2', 18, 18), IntelligentRobot('AGV-3', 2, 18)]
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

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HIVEMIND Digital Twin</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        * { box-sizing: border-box; }
        body { display: flex; font-family: 'Inter', sans-serif; margin: 0; height: 100vh; overflow: hidden; background: #0b0f19; color: #e2e8f0; }

        /* Glassmorphic Sidebar */
        #sidebar { 
            width: 350px; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(12px);
            border-right: 1px solid rgba(255,255,255,0.1); padding: 25px; display: flex; 
            flex-direction: column; gap: 20px; z-index: 10; box-shadow: 5px 0 25px rgba(0,0,0,0.5);
        }
        .header h2 { margin: 0; font-size: 22px; font-weight: 800; color: #38bdf8; letter-spacing: 1px; text-transform: uppercase; }
        .header p { margin: 5px 0 0 0; font-size: 12px; color: #94a3b8; }
        .section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin-bottom: -10px; font-weight: 600; }
        
        .palette-item { 
            background: rgba(30, 41, 59, 0.6); padding: 12px 15px; border-radius: 8px; cursor: grab; display: flex; 
            align-items: center; gap: 15px; border: 1px solid rgba(255,255,255,0.05); transition: 0.2s; font-size: 14px; margin-bottom: 10px;
        }
        .palette-item:hover { background: rgba(56, 189, 248, 0.15); border-color: #38bdf8; transform: translateY(-2px); }
        .color-dot { width: 14px; height: 14px; border-radius: 3px; }

        button.action-btn { padding: 12px; cursor: pointer; background: #ef4444; color: white; border: none; border-radius: 8px; font-weight: 600; transition: 0.2s; }
        button.action-btn:hover { background: #dc2626; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }

        #chat-container { display: flex; flex-direction: column; flex-grow: 1; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; overflow: hidden; background: rgba(0,0,0,0.3); }
        #chat { flex-grow: 1; overflow-y: auto; padding: 15px; font-family: 'Consolas', monospace; font-size: 12px; color: #cbd5e1; }
        .msg-sys { color: #34d399; margin-bottom: 8px; line-height: 1.4;}

        #main { flex-grow: 1; position: relative; display: flex; align-items: center; justify-content: center; padding: 20px; background: radial-gradient(circle at center, #1e293b 0%, #0b0f19 100%); }
        #canvas-container { 
            position: relative; width: 100%; max-width: 850px; aspect-ratio: 1/1; 
            border-radius: 12px; box-shadow: 0 0 50px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.05);
            background: #0f172a; overflow: hidden;
        }
        canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="header"><h2>HIVEMIND</h2><p>Digital Twin Dashboard</p></div>
        
        <div class="section-title">Environment Controls (Drag)</div>
        <div id="palette">
            <div class="palette-item" draggable="true" ondragstart="event.dataTransfer.setData('type', 'pallet')">
                <div class="color-dot" style="background: #d97706;"></div> Pallet Obstacle
            </div>
            <div class="palette-item" draggable="true" ondragstart="event.dataTransfer.setData('type', 'fire_extinguisher')">
                <div class="color-dot" style="background: #ef4444; border-radius: 50%;"></div> Fire Extinguisher
            </div>
            <div class="palette-item" draggable="true" ondragstart="event.dataTransfer.setData('type', 'human')">
                <div class="color-dot" style="background: #a855f7; border-radius: 50%;"></div> Moving Human
            </div>
        </div>

        <button class="action-btn" onclick="fetch('/reset')">Clear Dynamic Objects</button>

        <div class="section-title" style="margin-top: auto;">Terminal</div>
        <div id="chat-container">
            <div id="chat"><div class="msg-sys">[SYSTEM] Connection established.</div></div>
        </div>
    </div>
    
    <div id="main">
        <div id="canvas-container" ondrop="drop(event)" ondragover="event.preventDefault()">
            <canvas id="view"></canvas>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('view');
        const ctx = canvas.getContext('2d');
        let state = { robots: [], objects: {}, humans: [] };
        let timeCount = 0;
        
        function resize() {
            canvas.width = canvas.offsetWidth * window.devicePixelRatio;
            canvas.height = canvas.offsetHeight * window.devicePixelRatio;
        }
        window.addEventListener('resize', resize);
        resize();

        async function drop(ev) {
            ev.preventDefault();
            const type = ev.dataTransfer.getData("type");
            if (!type) return;
            const rect = canvas.getBoundingClientRect();
            const simX = (ev.clientX - rect.left) / rect.width * 20.0;
            const simY = (ev.clientY - rect.top) / rect.height * 20.0;
            const id = type + '_' + Math.floor(Math.random() * 10000);
            
            await fetch('/mutate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({op: 'add', id: id, class: type, pose: [simX, simY, 0]})
            });
            const chat = document.getElementById('chat');
            chat.innerHTML += '<div class="msg-sys">[EVENT] Placed ' + type + ' at (' + simX.toFixed(1) + ', ' + simY.toFixed(1) + ')</div>';
            chat.scrollTop = chat.scrollHeight;
        }

        function drawGrid(scale) {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
            ctx.lineWidth = 1;
            for(let i=0; i<=20; i++) {
                ctx.beginPath(); ctx.moveTo(i*scale, 0); ctx.lineTo(i*scale, 20*scale); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(0, i*scale); ctx.lineTo(20*scale, i*scale); ctx.stroke();
            }
        }

        function drawRobot(r, scale) {
            const x = r.x * scale;
            const y = r.y * scale;
            
            ctx.save();
            ctx.translate(x, y);
            
            // Path planning line
            if (r.path && r.path.length > 0) {
                ctx.save();
                ctx.rotate(-r.theta);
                ctx.beginPath();
                ctx.moveTo(0, 0);
                r.path.forEach(p => ctx.lineTo((p[0] - r.x) * scale, (p[1] - r.y) * scale));
                ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
                ctx.setLineDash([5, 5]);
                ctx.lineWidth = 2;
                ctx.stroke();
                ctx.restore();
            }

            ctx.rotate(r.theta);

            // Pulse ring
            const pulseRadius = 1.5 * scale + Math.sin(timeCount * 0.1) * 3;
            ctx.beginPath(); ctx.arc(0, 0, pulseRadius, 0, Math.PI*2);
            ctx.fillStyle = 'rgba(56, 189, 248, 0.05)'; ctx.fill();
            ctx.strokeStyle = r.state === 'YIELDING' ? 'rgba(245, 158, 11, 0.5)' : 'rgba(56, 189, 248, 0.3)';
            ctx.lineWidth = 2; ctx.stroke();
            
            // AGV Chassis
            const w = 0.8 * scale;
            const h = 0.5 * scale;
            ctx.fillStyle = '#1e293b';
            ctx.beginPath(); ctx.roundRect(-w/2, -h/2, w, h, 4); ctx.fill();
            ctx.strokeStyle = r.state === 'YIELDING' ? '#f59e0b' : '#38bdf8';
            ctx.lineWidth = 2; ctx.stroke();

            // Front LED
            ctx.fillStyle = '#34d399';
            ctx.beginPath(); ctx.arc(w/2 - 4, 0, 3, 0, Math.PI*2); ctx.fill();
            ctx.restore();
            
            // Label
            ctx.fillStyle = '#94a3b8'; ctx.font = '600 11px Inter'; ctx.textAlign = 'center';
            ctx.fillText(r.id, x, y - (0.8 * scale));
        }

        function drawObject(obj, scale) {
            const px = obj.pose[0] * scale;
            const py = obj.pose[1] * scale;
            const size = 0.8 * scale;
            
            ctx.save(); ctx.translate(px, py);
            if (obj.class === 'shelf') {
                ctx.fillStyle = '#1e293b'; ctx.beginPath(); ctx.roundRect(-size/2, -size/2, size, size, 4); ctx.fill();
                ctx.strokeStyle = 'rgba(255,255,255,0.1)'; ctx.lineWidth=2; ctx.stroke();
            } else if (obj.class === 'pallet') {
                ctx.fillStyle = '#d97706'; ctx.beginPath(); ctx.roundRect(-size/2.5, -size/2.5, size/1.2, size/1.2, 2); ctx.fill();
            } else if (obj.class === 'fire_extinguisher') {
                ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.arc(0, 0, size/3, 0, Math.PI*2); ctx.fill();
                ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(0, 0, size/8, 0, Math.PI*2); ctx.fill();
            } 
            ctx.restore();
        }

        function drawHuman(h, scale) {
            const px = h.x * scale;
            const py = h.y * scale;
            const size = 0.8 * scale;
            ctx.save(); ctx.translate(px, py);
            ctx.fillStyle = '#a855f7';
            ctx.beginPath(); ctx.arc(0, 0, size/3, 0, Math.PI*2); ctx.fill();
            ctx.strokeStyle = '#fff'; ctx.lineWidth=2;
            ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(size/3, 0); ctx.stroke(); 
            ctx.restore();
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const scale = Math.min(canvas.width, canvas.height) / 20.0;
            
            timeCount++;
            drawGrid(scale);
            
            for (const id in state.objects) { drawObject(state.objects[id], scale); }
            state.humans.forEach(h => drawHuman(h, scale));
            state.robots.forEach(r => drawRobot(r, scale));
            
            requestAnimationFrame(draw);
        }
        
        setInterval(async () => {
            try {
                const res = await fetch('/state');
                state = await res.json();
            } catch (e) {}
        }, 50);

        draw();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

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
    app.run(host='127.0.0.1', port=5006)
