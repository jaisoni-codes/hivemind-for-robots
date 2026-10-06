import os
import threading
import time
import math
import random
import heapq
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

def heuristic(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star_search(start, goal, obstacles, width=20, height=20):
    start_g = (round(start[0]), round(start[1]))
    goal_g = (round(goal[0]), round(goal[1]))
    
    frontier = []
    heapq.heappush(frontier, (0, start_g))
    came_from = {}
    cost_so_far = {}
    came_from[start_g] = None
    cost_so_far[start_g] = 0
    
    blocked = set()
    for obs in obstacles:
        # Only block the exact cell to prevent huge 3x3 deadzones
        blocked.add((round(obs[0]), round(obs[1])))
    
    # Never block the start or goal itself!
    if start_g in blocked: blocked.remove(start_g)
    if goal_g in blocked: blocked.remove(goal_g)

    while frontier:
        current = heapq.heappop(frontier)[1]
        if current == goal_g: break
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
            next_node = (current[0] + dx, current[1] + dy)
            if 0 <= next_node[0] <= width and 0 <= next_node[1] <= height:
                if next_node in blocked: continue
                new_cost = cost_so_far[current] + (1.414 if dx != 0 and dy != 0 else 1.0)
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + heuristic(goal_g, next_node)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current
                    
    if goal_g not in came_from: return []
    current = goal_g
    path = []
    while current != start_g:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

class DynamicHuman:
    def __init__(self, id, x, y):
        self.id = id; self.x = x; self.y = y; self.vx = 0; self.vy = 0; self.timer = 0
    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            angle = random.uniform(0, 2*math.pi)
            speed = 0.5
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.timer = random.uniform(2, 4)
        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt
        if 2 < nx < 18 and 2 < ny < 18:
            self.x = nx; self.y = ny
        else:
            self.timer = 0 

class IntelligentRobot:
    def __init__(self, r_id, x, y):
        self.id = r_id
        self.x = x; self.y = y; self.theta = 0
        self.v = 0; self.w = 0
        self.path = []
        self.target = None
        self.memory_obstacles = []
        self.state = 'EXPLORING'
        self.task = None
        self.task_timer = 0

    def assign_task(self, task):
        self.task = task
        self.target = (task['x'], task['y'])
        self.state = 'MOVING'
        self.replan()

    def replan(self):
        if not self.target: return
        self.path = a_star_search((self.x, self.y), self.target, self.memory_obstacles)

    def update(self, dt, all_robots, humans, truth_dict, central_memory):
        new_memory = []
        for obj_id, obj in truth_dict.items():
            dist = math.hypot(obj['pose'][0] - self.x, obj['pose'][1] - self.y)
            if dist < 4.0:
                noise = random.uniform(-0.05, 0.05) * dist
                px = obj['pose'][0] + noise; py = obj['pose'][1] + noise
                new_memory.append((px, py))
                central_memory[obj_id] = {'class': obj['class'], 'x': px, 'y': py, 'conf': 100, 'by': self.id, 'last_seen': time.time()}
        
        for h in humans:
            dist = math.hypot(h.x - self.x, h.y - self.y)
            if dist < 4.0:
                px = h.x + random.uniform(-0.1, 0.1) * dist
                py = h.y + random.uniform(-0.1, 0.1) * dist
                new_memory.append((px, py))
                central_memory[h.id] = {'class': 'human', 'x': px, 'y': py, 'conf': 100, 'by': self.id, 'last_seen': time.time()}

        if len(new_memory) != len(self.memory_obstacles):
            self.memory_obstacles = new_memory
            self.replan()

        # Task Logic
        if self.task:
            if self.state == 'WORKING':
                self.task_timer -= dt
                if self.task_timer <= 0:
                    self.task = None
                    self.state = 'EXPLORING'
                    self.target = None
                return 
            else:
                dist_to_target = math.hypot(self.target[0] - self.x, self.target[1] - self.y)
                if dist_to_target < 0.8:
                    self.state = 'WORKING'
                    self.task_timer = 2.0 
                    self.v = 0; self.w = 0
                elif len(self.path) == 0:
                    # Unreachable target! Abort task so robot doesn't freeze forever
                    self.task = None
                    self.state = 'EXPLORING'
        
        # Exploration Logic (Restored to completely free wandering anywhere)
        if not self.task:
            if self.target is None or len(self.path) == 0:
                self.target = (random.uniform(2, 18), random.uniform(2, 18))
                self.replan()
                self.state = 'EXPLORING'

        # Safety Shield
        safe_to_move = True
        for other in all_robots:
            if other.id != self.id:
                if math.hypot(other.x - self.x, other.y - self.y) < 1.5:
                    if self.id > other.id: safe_to_move = False
        for h in humans:
            if math.hypot(h.x - self.x, h.y - self.y) < 1.8: safe_to_move = False

        if not safe_to_move:
            self.v = 0; self.w = 0; self.state = 'YIELDING'
            return
        
        if self.task and self.state != 'WORKING': self.state = 'MOVING'
        if not self.task and self.state != 'WORKING' and self.state != 'YIELDING': self.state = 'EXPLORING'

        # Path Following
        if self.path:
            next_pt = self.path[0]
            dx = next_pt[0] - self.x; dy = next_pt[1] - self.y
            dist = math.hypot(dx, dy)
            if dist < 0.5:
                self.path.pop(0)
            else:
                target_theta = math.atan2(dy, dx)
                angle_diff = (target_theta - self.theta + math.pi) % (2 * math.pi) - math.pi
                self.w = max(-2.0, min(2.0, angle_diff * 3.0))
                if abs(angle_diff) < 0.5: self.v = 1.2
                else: self.v = 0.0
        else:
            self.v = 0; self.w = 0

        self.theta += self.w * dt
        self.theta = (self.theta + math.pi) % (2 * math.pi) - math.pi
        self.x += self.v * math.cos(self.theta) * dt
        self.y += self.v * math.sin(self.theta) * dt

class RealSimulator:
    def __init__(self):
        self.robots = [IntelligentRobot('AGV-1', 3, 3), IntelligentRobot('AGV-2', 17, 17), IntelligentRobot('AGV-3', 3, 17)]
        self.humans = []
        self.objects = {}
        self.central_memory = {}
        self.task_queue = []
        self.logs = []
        
        for y in range(5, 14): self.objects[f"r1_{y}"] = {"class": "shelf", "pose": [6, y, 0]}
        for y in range(5, 14): self.objects[f"r2_{y}"] = {"class": "shelf", "pose": [10, y, 0]}
        for y in range(5, 14): self.objects[f"r3_{y}"] = {"class": "shelf", "pose": [14, y, 0]}

    def step(self, dt):
        curr_time = time.time()
        for k, v in list(self.central_memory.items()):
            age = curr_time - v['last_seen']
            v['conf'] = max(0, 100 - int(age * 5))
            if v['conf'] == 0: del self.central_memory[k]

        while self.task_queue:
            task = self.task_queue[0]
            available_robots = [r for r in self.robots if r.task is None]
            if not available_robots:
                break
            available_robots.sort(key=lambda r: math.hypot(task['x'] - r.x, task['y'] - r.y))
            best_robot = available_robots[0]
            
            self.task_queue.pop(0)
            best_robot.assign_task(task)
            self.logs.append(f"[BRAIN] Dispatch '{task['name']}' -> {best_robot.id}")

        for h in self.humans: h.update(dt)
        for r in self.robots: r.update(dt, self.robots, self.humans, self.objects, self.central_memory)

sim = RealSimulator()

def sim_loop():
    last_time = time.time()
    while True:
        now = time.time()
        sim.step(now - last_time)
        last_time = now
        time.sleep(0.04)

threading.Thread(target=sim_loop, daemon=True).start()

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HIVEMIND Digital Twin</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; }
        body { display: flex; font-family: 'Inter', sans-serif; margin: 0; height: 100vh; overflow: hidden; background: #0b0f19; color: #e2e8f0; }
        .sidebar { width: 320px; background: rgba(15, 23, 42, 0.85); padding: 20px; display: flex; flex-direction: column; gap: 15px; z-index: 10; }
        #sidebar-left { border-right: 1px solid rgba(255,255,255,0.1); box-shadow: 5px 0 25px rgba(0,0,0,0.5); }
        #sidebar-right { border-left: 1px solid rgba(255,255,255,0.1); box-shadow: -5px 0 25px rgba(0,0,0,0.5); width: 400px; }
        .header h2 { margin: 0; font-size: 22px; font-weight: 800; color: #38bdf8; text-transform: uppercase; }
        .section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; font-weight: 600; }
        .palette-item { background: rgba(30, 41, 59, 0.6); padding: 10px; border-radius: 8px; cursor: grab; display: flex; align-items: center; gap: 15px; border: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
        .color-dot { width: 14px; height: 14px; border-radius: 3px; }
        
        .task-btn { padding: 4px 8px; cursor: pointer; background: #10b981; color: white; border: none; border-radius: 4px; font-weight: 600; font-size: 10px;}
        .task-btn:hover { background: #059669; }
        
        #chat-container { display: flex; flex-direction: column; flex-grow: 1; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: rgba(0,0,0,0.3); overflow:hidden;}
        #chat { flex-grow: 1; overflow-y: auto; padding: 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #cbd5e1; }
        
        #main { flex-grow: 1; display: flex; align-items: center; justify-content: center; padding: 20px; background: radial-gradient(circle at center, #1e293b 0%, #0b0f19 100%); }
        #canvas-container { position: relative; width: 100%; max-width: 850px; aspect-ratio: 1/1; border-radius: 12px; box-shadow: 0 0 50px rgba(0,0,0,0.8); background: #0f172a; overflow: hidden; }
        canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }

        table { width: 100%; border-collapse: collapse; font-family: 'JetBrains Mono', monospace; font-size: 11px; }
        th { text-align: left; padding: 8px; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.1); }
        td { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    </style>
</head>
<body>
    <div class="sidebar" id="sidebar-left">
        <div class="header"><h2>HIVEMIND</h2><p>Warehouse Command</p></div>
        
        <div class="section-title" style="margin-top:10px;">Environment (Drag)</div>
        <div id="palette">
            <div class="palette-item" draggable="true" ondragstart="event.dataTransfer.setData('type', 'pallet')">
                <div class="color-dot" style="background: #d97706;"></div> Pallet
            </div>
            <div class="palette-item" draggable="true" ondragstart="event.dataTransfer.setData('type', 'fire_extinguisher')">
                <div class="color-dot" style="background: #ef4444; border-radius: 50%;"></div> Extinguisher
            </div>
            <div class="palette-item" draggable="true" ondragstart="event.dataTransfer.setData('type', 'human')">
                <div class="color-dot" style="background: #a855f7; border-radius: 50%;"></div> Moving Human
            </div>
        </div>
        
        <div class="section-title" style="margin-top: auto;">Terminal Log</div>
        <div id="chat-container"><div id="chat"><div style="color:#34d399; margin-bottom:5px;">[SYSTEM] System Ready.</div></div></div>
    </div>
    
    <div id="main">
        <div id="canvas-container" ondrop="drop(event)" ondragover="event.preventDefault()">
            <canvas id="view"></canvas>
        </div>
    </div>

    <div class="sidebar" id="sidebar-right">
        <div class="header" style="margin-bottom: -10px;"><h2 style="color: #a855f7;">LIVING MEMORY</h2></div>
        <p style="font-size:11px; color:#94a3b8;">DISPATCH buttons will appear here once robots discover items.</p>
        <div style="flex-grow: 1; overflow-y: auto; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: rgba(0,0,0,0.2);">
            <table>
                <thead><tr><th>TYPE</th><th>POSE</th><th>CONF</th><th>ACTION</th></tr></thead>
                <tbody id="memory-body"></tbody>
            </table>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('view');
        const ctx = canvas.getContext('2d');
        let state = { robots: [], objects: {}, humans: [], memory: {}, logs: [] };
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
            await fetch('/mutate', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({op: 'add', class: type, pose: [simX, simY, 0]})
            });
        }

        async function sendTargetTask(objClass, x, y) {
            await fetch('/task', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({type: 'TARGETED', class: objClass, x: x, y: y})
            });
        }

        function drawWarehouse(scale) {
            ctx.fillStyle = 'rgba(52, 211, 153, 0.1)';
            ctx.fillRect(1*scale, 1*scale, 3*scale, 3*scale);
            ctx.strokeStyle = '#34d399'; ctx.lineWidth = 2; ctx.strokeRect(1*scale, 1*scale, 3*scale, 3*scale);
            ctx.fillStyle = '#34d399'; ctx.font = '10px Inter'; ctx.fillText('CHARGING ZONE', 2.5*scale, 0.8*scale);

            ctx.fillStyle = 'rgba(245, 158, 11, 0.1)';
            ctx.fillRect(8*scale, 17*scale, 8*scale, 3*scale);
            
            ctx.save(); ctx.beginPath(); ctx.rect(8*scale, 17*scale, 8*scale, 3*scale); ctx.clip();
            ctx.strokeStyle = 'rgba(245, 158, 11, 0.3)'; ctx.lineWidth = 10;
            for(let i=0; i<40; i++) {
                ctx.beginPath(); ctx.moveTo((8+i)*scale, 17*scale); ctx.lineTo((4+i)*scale, 20*scale); ctx.stroke();
            }
            ctx.restore();
            ctx.fillStyle = '#f59e0b'; ctx.fillText('LOADING DOCK', 12*scale, 16.5*scale);
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const scale = Math.min(canvas.width, canvas.height) / 20.0;
            
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)'; ctx.lineWidth = 1;
            for(let i=0; i<=20; i++) {
                ctx.beginPath(); ctx.moveTo(i*scale, 0); ctx.lineTo(i*scale, 20*scale); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(0, i*scale); ctx.lineTo(20*scale, i*scale); ctx.stroke();
            }

            drawWarehouse(scale);
            
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
            
            state.humans.forEach(h => {
                ctx.save(); ctx.translate(h.x*scale, h.y*scale);
                ctx.fillStyle = '#a855f7'; ctx.beginPath(); ctx.arc(0, 0, 0.25*scale, 0, Math.PI*2); ctx.fill();
                ctx.restore();
            });
            
            for (const id in state.memory) {
                const m = state.memory[id];
                if (m.class === 'shelf') continue;
                ctx.save(); ctx.translate(m.x*scale, m.y*scale);
                ctx.beginPath(); ctx.arc(0, 0, 8, 0, Math.PI*2);
                ctx.strokeStyle = '#f43f5e'; ctx.lineWidth = 2; ctx.setLineDash([2, 2]); ctx.stroke();
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
                if (r.state === 'YIELDING') color = '#f59e0b';
                else if (r.state === 'WORKING') color = '#10b981';
                else if (r.task) color = '#3b82f6';
                
                ctx.fillStyle = '#1e293b'; ctx.beginPath(); ctx.roundRect(-w/2, -h/2, w, h, 4); ctx.fill();
                ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
                ctx.fillStyle = color; ctx.beginPath(); ctx.arc(w/2 - 4, 0, 3, 0, Math.PI*2); ctx.fill();
                ctx.restore();
                
                ctx.fillStyle = '#94a3b8'; ctx.font = '600 11px Inter'; ctx.textAlign = 'center';
                let label = r.id;
                if(r.state === 'WORKING') label += " [WORKING]";
                ctx.fillText(label, x, y - (0.8 * scale));
            });
            
            requestAnimationFrame(draw);
        }
        
        setInterval(async () => {
            const res = await fetch('/state');
            state = await res.json();
            
            let html = '';
            const memEntries = Object.entries(state.memory).filter(([id, m]) => m.class !== 'shelf');
            
            if (memEntries.length === 0) {
                html = `<tr><td colspan="4" style="text-align:center; padding:20px; color:#64748b;">No items discovered yet.<br>Drag items to the grid to begin.</td></tr>`;
            } else {
                for (const [id, m] of memEntries) {
                    html += `<tr><td><b>${m.class.substring(0,6).toUpperCase()}</b></td><td>${m.x.toFixed(1)}, ${m.y.toFixed(1)}</td><td>${m.conf}%</td><td><button class="task-btn" onclick="sendTargetTask('${m.class}', ${m.x}, ${m.y})">DISPATCH</button></td></tr>`;
                }
            }
            document.getElementById('memory-body').innerHTML = html;

            const chat = document.getElementById('chat');
            if (state.logs.length > lastLogCount) {
                for(let i=lastLogCount; i<state.logs.length; i++) {
                    chat.innerHTML += `<div style="color:#34d399; margin-bottom:5px;">${state.logs[i]}</div>`;
                }
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
    humans = [{'x': h.x, 'y': h.y} for h in sim.humans]
    return jsonify({'robots': robots, 'objects': sim.objects, 'humans': humans, 'memory': sim.central_memory, 'logs': sim.logs})

@app.route('/mutate', methods=['POST'])
def mutate():
    data = request.json
    if data['class'] == 'human':
        sim.humans.append(DynamicHuman(f"h_{time.time()}", data['pose'][0], data['pose'][1]))
    else:
        sim.objects[f"obj_{time.time()}"] = data
    return jsonify({'status': 'ok'})

@app.route('/task', methods=['POST'])
def add_task():
    data = request.json
    if data['type'] == 'TARGETED':
        t_name = data['class'].upper()
        sim.task_queue.append({'name': t_name, 'x': data['x'], 'y': data['y']})
        sim.logs.append(f"[SYS] Targeted {t_name} queued at {data['x']:.1f}, {data['y']:.1f}")
        
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5018)
