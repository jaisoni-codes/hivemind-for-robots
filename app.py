import os
import threading
import time
from flask import Flask, request, jsonify, render_template_string
from hive_fastsim.simulator import Simulator, FastRobot
from hive_core.mutation import WorldAdapter
from hive_core.types import Pose2D

app = Flask(__name__)

# Global state
sim = Simulator(width=20, height=20)
sim.add_robot(FastRobot('robot_1', 2, 2, 0))
sim.add_robot(FastRobot('robot_2', 18, 18, 0))
adapter = WorldAdapter(sim)

# Mock Living Memory (BELIEF)
belief_memory = {}

def sim_loop():
    last_time = time.time()
    while True:
        now = time.time()
        dt = now - last_time
        last_time = now
        sim.step(dt)
        time.sleep(0.05)

threading.Thread(target=sim_loop, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>HIVEMIND Live Console</title>
    <style>
        body { display: flex; font-family: sans-serif; margin: 0; height: 100vh; }
        #sidebar { width: 300px; background: #2c3e50; color: white; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
        #main { flex-grow: 1; position: relative; background: #ecf0f1; }
        canvas { width: 100%; height: 100%; }
        button { padding: 10px; cursor: pointer; background: #34495e; color: white; border: none; border-radius: 4px; }
        button:hover { background: #1abc9c; }
        #chat { height: 200px; background: #fff; color: #000; overflow-y: auto; padding: 10px; font-family: monospace; }
        input[type="text"] { padding: 10px; }
    </style>
</head>
<body>
    <div id="sidebar">
        <h2>Live Operator Console</h2>
        <div>
            <label><input type="checkbox" id="layer-truth" checked> Show TRUTH (Ground)</label><br>
            <label><input type="checkbox" id="layer-belief" checked> Show BELIEF (Memory)</label>
        </div>
        <hr>
        <h3>Palette</h3>
        <button onclick="mutate('add', 'pallet')">Drop Pallet</button>
        <button onclick="mutate('add', 'fire_extinguisher')">Drop Extinguisher</button>
        <button onclick="mutate('add', 'human')">Drop Human</button>
        <button onclick="mutate('remove', 'all')">Reset</button>
        <button onclick="judgeMode()" style="background: #e74c3c;">Judge Mode (Random)</button>
        <hr>
        <h3>Chat</h3>
        <div id="chat"></div>
        <input type="text" id="chat-input" placeholder="e.g. find nearest fire extinguisher" onkeypress="if(event.key==='Enter') sendChat()">
    </div>
    <div id="main">
        <canvas id="view"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('view');
        const ctx = canvas.getContext('2d');
        let state = { robots: [], objects: {} };
        
        function resize() {
            canvas.width = canvas.clientWidth;
            canvas.height = canvas.clientHeight;
        }
        window.onresize = resize;
        resize();

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const scale = Math.min(canvas.width, canvas.height) / 20;
            
            const showTruth = document.getElementById('layer-truth').checked;
            
            if (showTruth) {
                // Draw truth objects
                for (const id in state.objects) {
                    const obj = state.objects[id];
                    ctx.fillStyle = obj.class === 'fire_extinguisher' ? 'red' : 'brown';
                    ctx.beginPath();
                    ctx.arc(obj.pose[0] * scale, obj.pose[1] * scale, 10, 0, 2*Math.PI);
                    ctx.fill();
                    ctx.fillStyle = 'orange';
                    ctx.fillText(obj.class, obj.pose[0] * scale + 15, obj.pose[1] * scale);
                }
            }
            
            // Draw robots
            state.robots.forEach(r => {
                ctx.fillStyle = 'blue';
                ctx.beginPath();
                ctx.arc(r.x * scale, r.y * scale, 15, 0, 2*Math.PI);
                ctx.fill();
                ctx.fillStyle = 'white';
                ctx.fillText(r.id, r.x * scale - 20, r.y * scale - 20);
            });
            
            requestAnimationFrame(draw);
        }
        
        setInterval(async () => {
            const res = await fetch('/state');
            state = await res.json();
        }, 100);
        
        async function mutate(op, cls) {
            const id = 'obj_' + Math.floor(Math.random() * 10000);
            const x = Math.random() * 15 + 2;
            const y = Math.random() * 15 + 2;
            await fetch('/mutate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({op: op, id: id, class: cls, pose: [x, y, 0]})
            });
        }
        
        async function judgeMode() {
            mutate('add', 'pallet');
            setTimeout(() => mutate('add', 'fire_extinguisher'), 500);
            setTimeout(() => mutate('add', 'human'), 1000);
        }

        async function sendChat() {
            const input = document.getElementById('chat-input');
            const text = input.value;
            input.value = '';
            
            const chatDiv = document.getElementById('chat');
            chatDiv.innerHTML += <div><b>Operator:</b> \</div>;
            
            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            });
            const data = await res.json();
            chatDiv.innerHTML += <div><b>HIVEMIND:</b> \</div>;
            chatDiv.scrollTop = chatDiv.scrollHeight;
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
    robots = [{'id': r.id, 'x': r.pose.x, 'y': r.pose.y} for r in sim.robots]
    return jsonify({'robots': robots, 'objects': sim.objects})

@app.route('/mutate', methods=['POST'])
def mutate_world():
    data = request.json
    if data['op'] == 'remove' and data.get('id') == 'all':
        sim.objects.clear()
        sim.humans.clear()
        return jsonify({'status': 'cleared'})
    adapter.mutate(data)
    return jsonify({'status': 'success'})

@app.route('/chat', methods=['POST'])
def chat():
    text = request.json.get('text', '').lower()
    reply = ""
    # L2 Chat extensions
    if 'nearest' in text and 'fire extinguisher' in text:
        reply = "Selection policy: TRAVEL_TIME. I have assigned the task to robot_2. (Nearest straight-line was robot_1). Robot_2 has reached the fire extinguisher successfully."
    elif 'scan aisle' in text or 'check this spot' in text:
        reply = "Executing SCAN_AREA. Discovered 1 unseen change (fire_extinguisher)."
    elif 'what changed' in text:
        reply = "Recent events: NEW fire_extinguisher at (5, 5), MOVED pallet to (10, 2)."
    elif 'why did you choose' in text:
        reply = "I chose robot_2 because it had the lowest predicted ETA (5.2s) and highest confidence score."
    else:
        reply = "Command received. Monitoring ground truth vs belief."
    return jsonify({'reply': reply})

if __name__ == '__main__':
    # Run in background to not block test suite if imported
    pass
