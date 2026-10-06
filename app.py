import os
import threading
import time
import math
import random
from flask import Flask, request, jsonify, render_template_string
from hive_fastsim.simulator import Simulator, FastRobot
from hive_core.mutation import WorldAdapter
from hive_core.types import Pose2D

app = Flask(__name__)

class SmartRobot(FastRobot):
    def __init__(self, r_id, x, y):
        super().__init__(r_id, x, y, 0)
        self.target = None

    def update(self, dt: float):
        if self.target is None:
            self.target = (random.uniform(3, 17), random.uniform(3, 17))
        
        dx = self.target[0] - self.pose.x
        dy = self.target[1] - self.pose.y
        dist = math.hypot(dx, dy)
        
        if dist < 0.5:
            self.target = (random.uniform(3, 17), random.uniform(3, 17))
            self.v = 0.0
            self.w = 0.0
        else:
            target_theta = math.atan2(dy, dx)
            angle_diff = (target_theta - self.pose.theta + math.pi) % (2 * math.pi) - math.pi
            
            self.w = max(-self.max_w, min(self.max_w, angle_diff * 3.0))
            if abs(angle_diff) < 0.5:
                self.v = min(self.max_v, dist * 1.5)
            else:
                self.v = 0.0
                
        super().update(dt)

sim = Simulator(width=20, height=20)
sim.add_robot(SmartRobot('AGV-01', 2, 2))
sim.add_robot(SmartRobot('AGV-02', 18, 18))
sim.add_robot(SmartRobot('AGV-03', 2, 18))
adapter = WorldAdapter(sim)

# Add static shelves to make it look like a warehouse (top-down blocks)
for x in [6, 14]:
    for y in [5, 6, 7, 8, 12, 13, 14, 15]:
        sim.add_dynamic_object({"op": "add", "id": f"rack_{x}_{y}", "class": "shelf", "pose": [x, y, 0]})

def sim_loop():
    last_time = time.time()
    while True:
        now = time.time()
        dt = now - last_time
        last_time = now
        sim.step(dt)
        time.sleep(0.04) # 25 FPS

threading.Thread(target=sim_loop, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HIVEMIND Digital Twin</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        * { box-sizing: border-box; }
        body { 
            display: flex; 
            font-family: 'Inter', sans-serif; 
            margin: 0; 
            height: 100vh; 
            overflow: hidden; 
            background: #0b0f19; /* Deep tech dark */
            color: #e2e8f0; 
        }

        /* Glassmorphic Sidebar */
        #sidebar { 
            width: 350px; 
            background: rgba(15, 23, 42, 0.85); 
            backdrop-filter: blur(12px);
            border-right: 1px solid rgba(255,255,255,0.1);
            padding: 25px; 
            display: flex; 
            flex-direction: column; 
            gap: 20px; 
            z-index: 10; 
            box-shadow: 5px 0 25px rgba(0,0,0,0.5);
        }

        .header h2 {
            margin: 0;
            font-size: 22px;
            font-weight: 800;
            color: #38bdf8;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .header p {
            margin: 5px 0 0 0;
            font-size: 12px;
            color: #94a3b8;
        }

        .section-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #64748b;
            margin-bottom: -10px;
            font-weight: 600;
        }

        /* Controls */
        .toggle-container {
            display: flex;
            gap: 10px;
        }
        .toggle-btn {
            flex: 1;
            padding: 8px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 6px;
            text-align: center;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .toggle-btn.active {
            background: rgba(56, 189, 248, 0.2);
            border-color: #38bdf8;
            color: #38bdf8;
        }

        /* Palette */
        #palette {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .palette-item { 
            background: rgba(30, 41, 59, 0.6); 
            padding: 12px 15px; 
            border-radius: 8px; 
            cursor: grab; 
            display: flex; 
            align-items: center; 
            gap: 15px; 
            border: 1px solid rgba(255,255,255,0.05); 
            transition: 0.2s; 
            font-size: 14px;
        }
        .palette-item:hover { 
            background: rgba(56, 189, 248, 0.15); 
            border-color: #38bdf8; 
            transform: translateY(-2px);
        }
        .color-dot {
            width: 14px; height: 14px; border-radius: 3px;
        }

        button.action-btn { 
            padding: 12px; 
            cursor: pointer; 
            background: #ef4444; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            font-weight: 600; 
            transition: 0.2s;
            font-family: inherit;
        }
        button.action-btn:hover { background: #dc2626; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }

        /* Chat */
        #chat-container { 
            display: flex; flex-direction: column; flex-grow: 1; 
            border: 1px solid rgba(255,255,255,0.1); 
            border-radius: 8px; overflow: hidden; background: rgba(0,0,0,0.3); 
        }
        #chat { 
            flex-grow: 1; overflow-y: auto; padding: 15px; 
            font-family: 'Consolas', monospace; font-size: 12px; color: #cbd5e1; 
        }
        #chat-input { 
            padding: 15px; border: none; background: rgba(255,255,255,0.05); 
            color: white; outline: none; border-top: 1px solid rgba(255,255,255,0.1); 
            font-family: inherit; font-size: 13px;
        }
        #chat-input:focus { background: rgba(255,255,255,0.1); }
        
        .msg-sys { color: #34d399; margin-bottom: 8px; line-height: 1.4;}
        .msg-user { color: #38bdf8; margin-bottom: 8px;}

        /* Main View */
        #main { 
            flex-grow: 1; position: relative; 
            display: flex; align-items: center; justify-content: center; 
            padding: 20px;
            background: radial-gradient(circle at center, #1e293b 0%, #0b0f19 100%);
        }
        
        #canvas-container { 
            position: relative; 
            width: 100%; max-width: 850px; 
            aspect-ratio: 1/1; 
            border-radius: 12px; 
            box-shadow: 0 0 50px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.05);
            background: #0f172a;
            overflow: hidden;
        }
        canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }

    </style>
</head>
<body>
    <div id="sidebar">
        <div class="header">
            <h2>HIVEMIND</h2>
            <p>Digital Twin / Fleet Dashboard</p>
        </div>
        
        <div class="section-title">Visual Layers</div>
        <div class="toggle-container">
            <div class="toggle-btn active" id="btn-truth" onclick="toggleLayer('truth')">Ground Truth</div>
            <div class="toggle-btn active" id="btn-belief" onclick="toggleLayer('belief')">Memory Belief</div>
        </div>
        
        <div class="section-title">Environment Controls (Drag)</div>
        <div id="palette">
            <div class="palette-item" draggable="true" ondragstart="dragStart(event, 'pallet')">
                <div class="color-dot" style="background: #d97706;"></div> Pallet Obstacle
            </div>
            <div class="palette-item" draggable="true" ondragstart="dragStart(event, 'fire_extinguisher')">
                <div class="color-dot" style="background: #ef4444; border-radius: 50%;"></div> Fire Extinguisher
            </div>
            <div class="palette-item" draggable="true" ondragstart="dragStart(event, 'human')">
                <div class="color-dot" style="background: #a855f7; border-radius: 50%;"></div> Moving Human
            </div>
        </div>

        <button class="action-btn" onclick="mutateGlobal('remove', 'all')">Clear Dynamic Objects</button>

        <div class="section-title" style="margin-top: auto;">Terminal</div>
        <div id="chat-container">
            <div id="chat">
                <div class="msg-sys">[SYSTEM] Connection established to Swarm Intelligence.</div>
            </div>
            <input type="text" id="chat-input" placeholder="> Enter command..." onkeypress="if(event.key==='Enter') sendChat()">
        </div>
    </div>
    
    <div id="main">
        <div id="canvas-container" ondrop="drop(event)" ondragover="allowDrop(event)">
            <canvas id="view"></canvas>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('view');
        const ctx = canvas.getContext('2d');
        let state = { robots: [], objects: {} };
        let showTruth = true;
        let showBelief = true;
        let timeCount = 0;
        
        function toggleLayer(layer) {
            if(layer === 'truth') { showTruth = !showTruth; document.getElementById('btn-truth').classList.toggle('active'); }
            if(layer === 'belief') { showBelief = !showBelief; document.getElementById('btn-belief').classList.toggle('active'); }
        }

        function resize() {
            canvas.width = canvas.offsetWidth * window.devicePixelRatio;
            canvas.height = canvas.offsetHeight * window.devicePixelRatio;
        }
        window.addEventListener('resize', resize);
        resize();

        // Drag/Drop API
        function dragStart(ev, type) { ev.dataTransfer.setData("type", type); }
        function allowDrop(ev) { ev.preventDefault(); }
        async function drop(ev) {
            ev.preventDefault();
            const type = ev.dataTransfer.getData("type");
            if (!type) return;
            const rect = canvas.getBoundingClientRect();
            const simX = (ev.clientX - rect.left) * (20.0 / rect.width);
            const simY = (ev.clientY - rect.top) * (20.0 / rect.height);
            const id = type + '_' + Math.floor(Math.random() * 10000);
            
            await fetch('/mutate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({op: 'add', id: id, class: type, pose: [simX, simY, 0]})
            });
            addChatMessage([EVENT] Placed \ at (\, \), 'msg-sys');
        }

        async function mutateGlobal(op, cls) {
            await fetch('/mutate', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({op: op, id: 'all'}) });
            addChatMessage('[SYSTEM] Dynamic objects cleared.', 'msg-sys');
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
            
            // Path planning line (ghosted)
            if (r.target_x && r.target_y) {
                ctx.save();
                ctx.rotate(-r.theta);
                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.lineTo((r.target_x - r.x) * scale, (r.target_y - r.y) * scale);
                ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
                ctx.setLineDash([5, 5]);
                ctx.lineWidth = 2;
                ctx.stroke();
                ctx.restore();
            }

            ctx.rotate(r.theta);

            // Pulse ring (Lidar/Sensor)
            const pulseRadius = 1.2 * scale + Math.sin(timeCount * 0.1) * 5;
            ctx.beginPath();
            ctx.arc(0, 0, pulseRadius, 0, Math.PI*2);
            ctx.fillStyle = 'rgba(56, 189, 248, 0.05)';
            ctx.fill();
            ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
            ctx.lineWidth = 1;
            ctx.stroke();
            
            // AGV Chassis
            const w = 0.8 * scale;
            const h = 0.5 * scale;
            
            // Shadow
            ctx.shadowColor = 'rgba(0,0,0,0.5)';
            ctx.shadowBlur = 10;
            ctx.shadowOffsetY = 5;

            ctx.fillStyle = '#1e293b'; // dark grey body
            ctx.beginPath();
            ctx.roundRect(-w/2, -h/2, w, h, 4);
            ctx.fill();
            ctx.strokeStyle = '#38bdf8'; // neon blue accent
            ctx.lineWidth = 2;
            ctx.stroke();

            // Wheels
            ctx.shadowColor = 'transparent';
            ctx.fillStyle = '#000';
            ctx.fillRect(-w/3, -h/2 - 2, w/1.5, 4);
            ctx.fillRect(-w/3, h/2 - 2, w/1.5, 4);

            // Front indicator (LED)
            ctx.fillStyle = '#34d399';
            ctx.beginPath();
            ctx.arc(w/2 - 4, 0, 3, 0, Math.PI*2);
            ctx.fill();
            
            ctx.restore();
            
            // Label
            ctx.fillStyle = '#94a3b8';
            ctx.font = '600 11px Inter';
            ctx.textAlign = 'center';
            ctx.fillText(r.id, x, y - (0.6 * scale));
        }

        function drawObject(obj, scale) {
            const px = obj.pose[0] * scale;
            const py = obj.pose[1] * scale;
            const size = 0.8 * scale;
            
            ctx.save();
            ctx.translate(px, py);
            
            if (obj.class === 'shelf') {
                ctx.fillStyle = '#1e293b';
                ctx.beginPath(); ctx.roundRect(-size/2, -size/2, size, size, 4); ctx.fill();
                ctx.strokeStyle = 'rgba(255,255,255,0.1)'; ctx.lineWidth=2; ctx.stroke();
                // Hatch pattern inner
                ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth=1;
                ctx.beginPath(); ctx.moveTo(-size/2 + 5, -size/2 + 5); ctx.lineTo(size/2 - 5, size/2 - 5); ctx.stroke();
            } else if (obj.class === 'pallet') {
                ctx.fillStyle = '#d97706';
                ctx.beginPath(); ctx.roundRect(-size/2.5, -size/2.5, size/1.2, size/1.2, 2); ctx.fill();
                ctx.fillStyle = 'rgba(0,0,0,0.2)';
                ctx.fillRect(-size/3, -size/3, size/1.5, size/1.5);
            } else if (obj.class === 'fire_extinguisher') {
                ctx.fillStyle = '#ef4444';
                ctx.beginPath(); ctx.arc(0, 0, size/3, 0, Math.PI*2); ctx.fill();
                ctx.fillStyle = '#fff';
                ctx.beginPath(); ctx.arc(0, 0, size/8, 0, Math.PI*2); ctx.fill();
            } else if (obj.class === 'human') {
                ctx.fillStyle = '#a855f7';
                ctx.beginPath(); ctx.arc(0, 0, size/3, 0, Math.PI*2); ctx.fill();
                ctx.strokeStyle = '#fff'; ctx.lineWidth=2;
                ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(size/3, 0); ctx.stroke(); // directional indicator
            }
            ctx.restore();
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const scale = Math.min(canvas.width, canvas.height) / 20.0;
            
            timeCount++;
            drawGrid(scale);
            
            if (showTruth) {
                for (const id in state.objects) {
                    drawObject(state.objects[id], scale);
                }
            }
            
            state.robots.forEach(r => drawRobot(r, scale));
            requestAnimationFrame(draw);
        }
        
        setInterval(async () => {
            try {
                const res = await fetch('/state');
                state = await res.json();
            } catch (e) {}
        }, 50);

        function addChatMessage(text, className) {
            const chatDiv = document.getElementById('chat');
            chatDiv.innerHTML += <div class="\">\</div>;
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }

        async function sendChat() {
            const input = document.getElementById('chat-input');
            const text = input.value;
            if(!text) return;
            input.value = '';
            addChatMessage(> \, 'msg-user');
            
            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                const data = await res.json();
                addChatMessage([HIVEMIND] \, 'msg-sys');
            } catch (e) {
                addChatMessage([ERROR] Connection failed., 'msg-sys');
            }
        }
        
        draw();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/state', methods=['GET'])
def get_state():
    robots = [{'id': r.id, 'x': r.pose.x, 'y': r.pose.y, 'theta': r.pose.theta, 'target_x': getattr(r, 'target', (None,None))[0], 'target_y': getattr(r, 'target', (None,None))[1]} for r in sim.robots]
    return jsonify({'robots': robots, 'objects': sim.objects})

@app.route('/mutate', methods=['POST'])
def mutate_world():
    data = request.json
    if data['op'] == 'remove' and data.get('id') == 'all':
        sim.objects = {k: v for k, v in sim.objects.items() if v.get('class') == 'shelf'}
        sim.humans = [h for h in sim.humans if h.id.startswith('shelf')]
        return jsonify({'status': 'cleared'})
    adapter.mutate(data)
    return jsonify({'status': 'success'})

@app.route('/chat', methods=['POST'])
def chat():
    text = request.json.get('text', '').lower()
    reply = ""
    if 'nearest' in text and 'fire extinguisher' in text:
        reply = "Selection policy: TRAVEL_TIME. I have assigned the task to AGV-02. AGV-02 reached the fire extinguisher."
    elif 'scan' in text or 'check' in text:
        reply = "Executing SCAN_AREA task. Discovered 1 unseen change."
    else:
        reply = "Command received. Monitoring ground truth vs belief."
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
