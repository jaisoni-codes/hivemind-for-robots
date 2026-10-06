import os
import threading
import time
import math
import random
import heapq
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- ROBUST WAREHOUSE PHYSICS & PATHFINDING ---
# 20x20m warehouse, 0.5m grid cells
GRID = 0.5
W = int(20 / GRID)
H = int(20 / GRID)

def get_blocked_cells(objects, all_robots, my_id=None):
    blocked = set()
    
    # 1. Static & Dynamic Objects (Shelves, Pallets)
    for obj in objects.values():
        if obj['class'] in ['shelf', 'pallet', 'fire_extinguisher']:
            cx, cy = int(obj['pose'][0]/GRID), int(obj['pose'][1]/GRID)
            blocked.add((cx, cy))
            blocked.add((cx+1, cy)); blocked.add((cx-1, cy))
            blocked.add((cx, cy+1)); blocked.add((cx, cy-1))
            if obj['class'] == 'shelf': # Shelves are longer
                blocked.add((cx, cy+2)); blocked.add((cx, cy-2))
                
    # 2. Other Robots (Dynamic Obstacles)
    for r in all_robots:
        if r.id != my_id:
            rx, ry = int(r.x/GRID), int(r.y/GRID)
            blocked.add((rx, ry))
            # Inflate robot by 1 cell (0.5m) to ensure clearance
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (-1,1), (1,-1)]:
                blocked.add((rx+dx, ry+dy))
                
    return blocked

def get_free_target(tx, ty, blocked):
    cx, cy = int(tx/GRID), int(ty/GRID)
    queue = [(cx, cy)]
    visited = set(queue)
    while queue:
        curr = queue.pop(0)
        if curr not in blocked:
            return (curr[0]*GRID, curr[1]*GRID)
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
            nx, ny = curr[0]+dx, curr[1]+dy
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
    return (tx, ty)

def a_star(start_pt, goal_pt, blocked):
    start = (int(start_pt[0]/GRID), int(start_pt[1]/GRID))
    goal = (int(goal_pt[0]/GRID), int(goal_pt[1]/GRID))
    
    if start in blocked: blocked.remove(start)
    if goal in blocked: blocked.remove(goal)
    
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    
    while frontier:
        current = heapq.heappop(frontier)[1]
        if current == goal: break
        
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
            nx, ny = current[0]+dx, current[1]+dy
            if 0 <= nx < W and 0 <= ny < H:
                if (nx, ny) in blocked: continue
                cost = 1.414 if dx != 0 and dy != 0 else 1.0
                new_cost = cost_so_far[current] + cost
                if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                    cost_so_far[(nx, ny)] = new_cost
                    priority = new_cost + math.hypot(goal[0]-nx, goal[1]-ny)
                    heapq.heappush(frontier, (priority, (nx, ny)))
                    came_from[(nx, ny)] = current
                    
    if goal not in came_from: return []
    path = []
    curr = goal
    while curr != start:
        path.append((curr[0]*GRID, curr[1]*GRID))
        curr = came_from[curr]
    path.reverse()
    return path

class WarehouseAGV:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x; self.y = y; self.theta = 0
        self.v = 0; self.w = 0
        self.path = []
        self.target = None
        self.task = None
        self.state = 'EXPLORING'
        self.timer = 0
        self.replan_timer = 0

    def assign_task(self, task, objects, all_robots):
        self.task = task
        blocked = get_blocked_cells(objects, all_robots, self.id)
        # Target a free cell next to the object, never ON the object
        self.target = get_free_target(task['x'], task['y'], blocked)
        self.state = 'MOVING'
        self.replan(objects, all_robots)

    def replan(self, objects, all_robots):
        if not self.target: return
        blocked = get_blocked_cells(objects, all_robots, self.id)
        self.path = a_star((self.x, self.y), self.target, blocked)
        if not self.path:
            # If completely blocked, just stop and wait
            self.v = 0; self.w = 0

    def update(self, dt, all_robots, objects, memory):
        # 1. Update Sensors
        for obj_id, obj in objects.items():
            if obj['class'] != 'shelf':
                dist = math.hypot(obj['pose'][0]-self.x, obj['pose'][1]-self.y)
                if dist < 4.0:
                    memory[obj_id] = {'class': obj['class'], 'x': obj['pose'][0], 'y': obj['pose'][1], 'conf': 100, 'last': time.time()}

        # 2. Replan periodically to route around moving obstacles
        self.replan_timer -= dt
        if self.replan_timer <= 0:
            self.replan_timer = 1.0 # Replan every 1 second
            if self.state in ['MOVING', 'EXPLORING'] and self.target:
                self.replan(objects, all_robots)

        # 3. State Machine Logic
        if self.task:
            # Check distance to ACTUAL task object, not the offset target
            dist_to_task = math.hypot(self.task['x'] - self.x, self.task['y'] - self.y)
            if dist_to_task < 2.0:
                self.state = 'WORKING'
                self.timer += dt
                self.v = 0; self.w = 0
                if self.timer > 3.0: # Task complete after 3 seconds
                    self.task = None
                    self.target = None
                    self.state = 'EXPLORING'
                    self.timer = 0
            else:
                self.state = 'MOVING'
        else:
            if not self.target or len(self.path) == 0:
                # Pick random free exploration point
                blocked = get_blocked_cells(objects, all_robots, self.id)
                self.target = get_free_target(random.uniform(2,18), random.uniform(2,18), blocked)
                self.replan(objects, all_robots)
                self.state = 'EXPLORING'

        # 4. Strict Collision Prevention (Override)
        safe = True
        for other in all_robots:
            if other.id != self.id:
                dist = math.hypot(other.x - self.x, other.y - self.y)
                if dist < 1.2:
                    # Priority based yielding to prevent deadlocks
                    if self.id > other.id: safe = False

        if not safe:
            self.v = 0; self.w = 0
            return

        # 5. Pure Pursuit Kinematic Controller
        if self.path and self.state != 'WORKING':
            carrot = self.path[0]
            dx = carrot[0] - self.x
            dy = carrot[1] - self.y
            dist = math.hypot(dx, dy)
            
            if dist < 0.6:
                self.path.pop(0)
            else:
                target_th = math.atan2(dy, dx)
                diff = (target_th - self.theta + math.pi) % (2*math.pi) - math.pi
                
                self.w = max(-2.5, min(2.5, diff * 4.0))
                if abs(diff) < 0.2: self.v = 1.5
                elif abs(diff) < 0.8: self.v = 0.8
                else: self.v = 0.0
        else:
            self.v = 0; self.w = 0

        # 6. Apply Movement with Hard Boundary Check
        nx = self.x + self.v * math.cos(self.theta) * dt
        ny = self.y + self.v * math.sin(self.theta) * dt
        
        # Hard check against static obstacles
        hard_collision = False
        for obj in objects.values():
            if obj['class'] == 'shelf':
                if abs(nx - obj['pose'][0]) < 1.0 and abs(ny - obj['pose'][1]) < 1.5:
                    hard_collision = True
                    break
        
        if not hard_collision and 0.5 < nx < 19.5 and 0.5 < ny < 19.5:
            self.x = nx
            self.y = ny
        else:
            # If hit wall, stop and force replan
            self.v = 0; self.path = []; self.replan_timer = 0
            
        self.theta += self.w * dt
        self.theta = (self.theta + math.pi) % (2*math.pi) - math.pi

class Engine:
    def __init__(self):
        self.robots = [WarehouseAGV('AGV-1', 2, 2), WarehouseAGV('AGV-2', 18, 18), WarehouseAGV('AGV-3', 2, 18)]
        self.objects = {}
        for y in range(5, 14): self.objects[f"r1_{y}"] = {"class": "shelf", "pose": [6, y, 0]}
        for y in range(5, 14): self.objects[f"r2_{y}"] = {"class": "shelf", "pose": [10, y, 0]}
        for y in range(5, 14): self.objects[f"r3_{y}"] = {"class": "shelf", "pose": [14, y, 0]}
        self.memory = {}
        self.tasks = []
        self.logs = []

    def step(self, dt):
        curr = time.time()
        for k, v in list(self.memory.items()):
            age = curr - v['last']
            v['conf'] = max(0, 100 - int(age * 5))
            if v['conf'] == 0: del self.memory[k]

        if self.tasks:
            task = self.tasks[0]
            avail = [r for r in self.robots if r.task is None]
            if avail:
                avail.sort(key=lambda r: math.hypot(task['x']-r.x, task['y']-r.y))
                best = avail[0]
                self.tasks.pop(0)
                best.assign_task(task, self.objects, self.robots)
                self.logs.append(f"[DISPATCH] {task['name']} assigned to {best.id} (Nearest)")

        for r in self.robots:
            r.update(dt, self.robots, self.objects, self.memory)

sim = Engine()

def loop():
    last = time.time()
    while True:
        now = time.time()
        sim.step(now - last)
        last = now
        time.sleep(0.04)

threading.Thread(target=loop, daemon=True).start()

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HIVEMIND Rebuilt</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; }
        body { display: flex; font-family: 'Inter', sans-serif; margin: 0; height: 100vh; overflow: hidden; background: #0b0f19; color: #e2e8f0; }
        .sidebar { width: 320px; background: rgba(15, 23, 42, 0.85); padding: 20px; display: flex; flex-direction: column; gap: 15px; z-index: 10; }
        #sidebar-left { border-right: 1px solid rgba(255,255,255,0.1); }
        #sidebar-right { border-left: 1px solid rgba(255,255,255,0.1); width: 400px; }
        .header h2 { margin: 0; font-size: 22px; font-weight: 800; color: #38bdf8; text-transform: uppercase; }
        .palette-item { background: rgba(30, 41, 59, 0.6); padding: 10px; border-radius: 8px; cursor: grab; display: flex; align-items: center; gap: 15px; border: 1px solid rgba(255,255,255,0.05); }
        .color-dot { width: 14px; height: 14px; border-radius: 3px; }
        .task-btn { padding: 6px 12px; cursor: pointer; background: #3b82f6; color: white; border: none; border-radius: 4px; font-weight: bold; width:100%;}
        .task-btn:hover { background: #2563eb; }
        #chat { flex-grow: 1; overflow-y: auto; padding: 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: rgba(0,0,0,0.3); border-radius: 8px;}
        #main { flex-grow: 1; display: flex; align-items: center; justify-content: center; padding: 20px; }
        #canvas-container { position: relative; width: 100%; max-width: 850px; aspect-ratio: 1/1; border-radius: 12px; background: #0f172a; overflow: hidden; }
        canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th, td { text-align: left; padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    </style>
</head>
<body>
    <div class="sidebar" id="sidebar-left">
        <div class="header"><h2>HIVEMIND</h2><p>V13 Robust Physics</p></div>
        <div id="palette">
            <div class="palette-item" draggable="true" ondragstart="event.dataTransfer.setData('type', 'pallet')"><div class="color-dot" style="background: #d97706;"></div> Pallet</div>
            <div class="palette-item" draggable="true" ondragstart="event.dataTransfer.setData('type', 'fire_extinguisher')"><div class="color-dot" style="background: #ef4444; border-radius: 50%;"></div> Extinguisher</div>
        </div>
        <div id="chat"><div style="color:#34d399;">[SYS] Ultimate Physics Engine Online.</div></div>
    </div>
    
    <div id="main">
        <div id="canvas-container" ondrop="drop(event)" ondragover="event.preventDefault()"><canvas id="view"></canvas></div>
    </div>

    <div class="sidebar" id="sidebar-right">
        <div class="header"><h2>LIVING MEMORY</h2></div>
        <div style="flex-grow: 1; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 8px;">
            <table>
                <thead><tr><th>TYPE</th><th>POSE</th><th>CONF</th><th>ACTION</th></tr></thead>
                <tbody id="memory-body"></tbody>
            </table>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('view');
        const ctx = canvas.getContext('2d');
        let state = { robots: [], objects: {}, memory: {}, logs: [] };
        let lastLogCount = 0;
        
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
            await fetch('/mutate', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({class: type, pose: [simX, simY, 0]}) });
        }

        async function sendTask(cls, x, y) {
            await fetch('/task', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({class: cls, x: x, y: y}) });
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const scale = Math.min(canvas.width, canvas.height) / 20.0;
            
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)'; ctx.lineWidth = 1;
            for(let i=0; i<=20; i++) {
                ctx.beginPath(); ctx.moveTo(i*scale, 0); ctx.lineTo(i*scale, 20*scale); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(0, i*scale); ctx.lineTo(20*scale, i*scale); ctx.stroke();
            }
            
            for (const id in state.objects) {
                const obj = state.objects[id];
                const px = obj.pose[0] * scale; const py = obj.pose[1] * scale; const size = 0.8 * scale;
                ctx.save(); ctx.translate(px, py);
                if (obj.class === 'shelf') {
                    ctx.fillStyle = '#1e293b'; ctx.beginPath(); ctx.roundRect(-size/2, -size/1.2, size, size*1.5, 4); ctx.fill();
                    ctx.strokeStyle = 'rgba(255,255,255,0.1)'; ctx.lineWidth=2; ctx.stroke();
                } else if (obj.class === 'pallet') {
                    ctx.fillStyle = '#d97706'; ctx.beginPath(); ctx.roundRect(-size/2.5, -size/2.5, size/1.2, size/1.2, 2); ctx.fill();
                } else if (obj.class === 'fire_extinguisher') {
                    ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.arc(0, 0, size/3, 0, Math.PI*2); ctx.fill();
                } 
                ctx.restore();
            }
            
            state.robots.forEach(r => {
                const x = r.x * scale; const y = r.y * scale;
                ctx.save(); ctx.translate(x, y);
                
                if (r.path && r.path.length > 0) {
                    ctx.save(); ctx.rotate(-r.theta); ctx.beginPath(); ctx.moveTo(0, 0);
                    r.path.forEach(p => ctx.lineTo((p[0] - r.x) * scale, (p[1] - r.y) * scale));
                    ctx.strokeStyle = r.task ? '#3b82f6' : 'rgba(255,255,255,0.2)'; 
                    ctx.setLineDash([5, 5]); ctx.lineWidth = 2; ctx.stroke();
                    ctx.restore();
                }
                ctx.rotate(r.theta);
                
                const w = 0.8 * scale; const h = 0.5 * scale;
                let color = '#38bdf8'; 
                if (r.state === 'WORKING') color = '#10b981';
                else if (r.task) color = '#3b82f6';
                
                ctx.fillStyle = '#1e293b'; ctx.beginPath(); ctx.roundRect(-w/2, -h/2, w, h, 4); ctx.fill();
                ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
                ctx.fillStyle = color; ctx.beginPath(); ctx.arc(w/2 - 4, 0, 3, 0, Math.PI*2); ctx.fill();
                ctx.restore();
                
                ctx.fillStyle = '#94a3b8'; ctx.font = '600 11px Inter'; ctx.textAlign = 'center';
                ctx.fillText(r.id + (r.state==='WORKING'?' [WORK]':''), x, y - (0.8 * scale));
            });
            
            requestAnimationFrame(draw);
        }
        
        setInterval(async () => {
            const res = await fetch('/state');
            state = await res.json();
            
            let html = '';
            for (const [id, m] of Object.entries(state.memory)) {
                html += `<tr><td><b>${m.class.toUpperCase()}</b></td><td>${m.x.toFixed(1)}, ${m.y.toFixed(1)}</td><td>${m.conf}%</td>
                    <td><button class="task-btn" onclick="sendTask('${m.class}', ${m.x}, ${m.y})">DISPATCH</button></td></tr>`;
            }
            document.getElementById('memory-body').innerHTML = html;

            const chat = document.getElementById('chat');
            if (state.logs.length > lastLogCount) {
                for(let i=lastLogCount; i<state.logs.length; i++) chat.innerHTML += `<div style="color:#34d399; margin-bottom:5px;">${state.logs[i]}</div>`;
                chat.scrollTop = chat.scrollHeight;
                lastLogCount = state.logs.length;
            }
        }, 100);
        draw();
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return HTML

@app.route('/state')
def get_state():
    robots = [{'id': r.id, 'x': r.x, 'y': r.y, 'theta': r.theta, 'path': r.path, 'state': r.state, 'task': r.task} for r in sim.robots]
    return jsonify({'robots': robots, 'objects': sim.objects, 'memory': sim.memory, 'logs': sim.logs[-30:]})

@app.route('/mutate', methods=['POST'])
def mutate():
    sim.objects[f"obj_{time.time()}"] = request.json
    return jsonify({'status': 'ok'})

@app.route('/task', methods=['POST'])
def add_task():
    sim.tasks.append({'name': request.json['class'].upper(), 'x': request.json['x'], 'y': request.json['y']})
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5026)
