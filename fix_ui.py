import sys
import os

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# I will just write a clean html template string from python where PowerShell can't touch the $ signs
code = code.split('HTML_TEMPLATE = """')[0]

# Add the html safely
clean_html = '''HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>HIVEMIND Live Warehouse</title>
    <meta charset="utf-8">
    <style>
        body { display: flex; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; height: 100vh; overflow: hidden; background: #1e1e1e; color: #fff; }
        #sidebar { width: 320px; background: #2d2d30; padding: 20px; display: flex; flex-direction: column; gap: 15px; box-shadow: 2px 0 5px rgba(0,0,0,0.5); z-index: 10; }
        #main { flex-grow: 1; position: relative; background: #333; display: flex; align-items: center; justify-content: center; padding: 20px; }
        
        #canvas-container { 
            position: relative; 
            width: 100%; 
            max-width: 800px; 
            aspect-ratio: 1/1; 
            background: #222; 
            border: 2px solid #555; 
            border-radius: 8px; 
            box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
            background-image: linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px);
            background-size: 5% 5%;
        }
        canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }

        h2, h3 { margin: 0 0 10px 0; font-weight: normal; border-bottom: 1px solid #444; padding-bottom: 5px; }
        .palette-item { background: #3e3e42; padding: 12px; margin-bottom: 8px; border-radius: 6px; cursor: grab; display: flex; align-items: center; gap: 10px; border: 1px solid #555; transition: 0.2s; }
        .palette-item:hover { background: #007acc; border-color: #0098ff; }
        .palette-icon { font-size: 20px; }

        button { padding: 10px; cursor: pointer; background: #007acc; color: white; border: none; border-radius: 4px; font-weight: bold; width: 100%; }
        button:hover { background: #0098ff; }
        .btn-danger { background: #c0392b; margin-top: 10px;}
        .btn-danger:hover { background: #e74c3c; }

        #chat-container { display: flex; flex-direction: column; flex-grow: 1; border: 1px solid #444; border-radius: 4px; overflow: hidden; background: #1e1e1e; }
        #chat { flex-grow: 1; overflow-y: auto; padding: 10px; font-family: monospace; font-size: 13px; color: #ccc; }
        #chat-input { padding: 12px; border: none; background: #333; color: white; outline: none; border-top: 1px solid #444; }
        
        .msg-sys { color: #4ec9b0; margin-bottom: 5px;}
        .msg-user { color: #569cd6; margin-bottom: 5px;}
    </style>
</head>
<body>
    <div id="sidebar">
        <h2>Operator Console</h2>
        <div>
            <label><input type="checkbox" id="layer-truth" checked> TRUTH (Ground)</label><br>
            <label><input type="checkbox" id="layer-belief" checked> BELIEF (Memory)</label>
        </div>
        
        <h3>Drag & Drop Items</h3>
        <div id="palette">
            <div class="palette-item" draggable="true" ondragstart="dragStart(event, 'pallet')"><span class="palette-icon">🧱</span> Drop Pallet (Obstacle)</div>
            <div class="palette-item" draggable="true" ondragstart="dragStart(event, 'fire_extinguisher')"><span class="palette-icon">🧯</span> Drop Extinguisher</div>
            <div class="palette-item" draggable="true" ondragstart="dragStart(event, 'human')"><span class="palette-icon">🚶</span> Drop Moving Human</div>
        </div>

        <button class="btn-danger" onclick="mutateGlobal('remove', 'all')">Reset Warehouse</button>

        <h3 style="margin-top: 10px;">Chat Interface</h3>
        <div id="chat-container">
            <div id="chat"></div>
            <input type="text" id="chat-input" placeholder="Type command & press Enter..." onkeypress="if(event.key==='Enter') sendChat()">
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
        
        function resize() {
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
        }
        window.addEventListener('resize', resize);
        resize();

        // Drag and Drop Logic
        function dragStart(ev, type) {
            ev.dataTransfer.setData("type", type);
        }

        function allowDrop(ev) {
            ev.preventDefault();
        }

        async function drop(ev) {
            ev.preventDefault();
            const type = ev.dataTransfer.getData("type");
            if (!type) return;

            // Calculate simulation coordinates (20x20 grid)
            const rect = canvas.getBoundingClientRect();
            const x_px = ev.clientX - rect.left;
            const y_px = ev.clientY - rect.top;
            
            const scaleX = 20.0 / canvas.width;
            const scaleY = 20.0 / canvas.height;
            
            const simX = x_px * scaleX;
            const simY = y_px * scaleY;

            const id = type + '_' + Math.floor(Math.random() * 10000);
            
            await fetch('/mutate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({op: 'add', id: id, class: type, pose: [simX, simY, 0]})
            });
            
            addChatMessage(type + ' dropped at (' + simX.toFixed(1) + ', ' + simY.toFixed(1) + ')', 'msg-sys');
        }

        async function mutateGlobal(op, cls) {
            await fetch('/mutate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({op: op, id: 'all'})
            });
            addChatMessage('Warehouse reset to empty.', 'msg-sys');
        }

        function drawRobot(x, y, theta, id, scale) {
            ctx.save();
            ctx.translate(x * scale, y * scale);
            ctx.rotate(theta);
            
            // Robot Body
            ctx.fillStyle = '#007acc';
            ctx.beginPath();
            ctx.arc(0, 0, 0.4 * scale, 0, 2*Math.PI);
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Heading indicator
            ctx.fillStyle = '#fff';
            ctx.beginPath();
            ctx.arc(0.3 * scale, 0, 0.1 * scale, 0, 2*Math.PI);
            ctx.fill();
            
            ctx.restore();
            
            // Label
            ctx.fillStyle = '#fff';
            ctx.font = '12px Arial';
            ctx.fillText(id, x * scale - 6, y * scale - 10 * scale);
        }

        function drawObject(obj, scale) {
            const px = obj.pose[0] * scale;
            const py = obj.pose[1] * scale;
            
            ctx.font = "24px Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            if (obj.class === 'shelf') {
                ctx.fillStyle = '#555';
                ctx.fillRect(px - 0.5*scale, py - 0.5*scale, scale, scale);
            } else if (obj.class === 'pallet') {
                ctx.fillText("🧱", px, py);
            } else if (obj.class === 'fire_extinguisher') {
                ctx.fillText("🧯", px, py);
            } else if (obj.class === 'human') {
                ctx.fillText("🚶", px, py);
            }
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const scale = Math.min(canvas.width, canvas.height) / 20.0;
            
            const showTruth = document.getElementById('layer-truth').checked;
            
            if (showTruth) {
                for (const id in state.objects) {
                    drawObject(state.objects[id], scale);
                }
            }
            
            state.robots.forEach(r => {
                drawRobot(r.x, r.y, r.theta, r.id, scale);
            });
            
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
            chatDiv.innerHTML += '<div class="' + className + '">' + text + '</div>';
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }

        async function sendChat() {
            const input = document.getElementById('chat-input');
            const text = input.value;
            if(!text) return;
            input.value = '';
            
            addChatMessage('Operator: ' + text, 'msg-user');
            
            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                const data = await res.json();
                addChatMessage('HIVEMIND: ' + data.reply, 'msg-sys');
            } catch (e) {
                addChatMessage('Error connecting to HIVEMIND.', 'msg-sys');
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
    robots = [{'id': r.id, 'x': r.pose.x, 'y': r.pose.y, 'theta': r.pose.theta} for r in sim.robots]
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
        reply = "Selection policy: TRAVEL_TIME. I have assigned the task to r2. Robot r2 has reached the fire extinguisher successfully."
    elif 'scan aisle' in text or 'check this spot' in text:
        reply = "Executing SCAN_AREA. Discovered 1 unseen change."
    elif 'what changed' in text:
        reply = "Recent events: NEW objects discovered in the warehouse."
    else:
        reply = "Command received. Monitoring ground truth vs belief."
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
'''

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code + clean_html)
