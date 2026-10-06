import os
import csv
import yaml
import json

def build_lab():
    csv_file = 'results/scenarios.csv'
    yaml_dir = 'scenarios/yaml'
    
    if not os.path.exists(csv_file):
        print("Error: results/scenarios.csv not found. Run tests/test_a2_harness.py first.")
        return
        
    # Read CSV
    results = {}
    baseline_passes = 0
    hivemind_passes = 0
    total = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_id = int(row['id'])
            b_pass = row['baseline_pass'] == 'True'
            h_pass = row['hivemind_pass'] == 'True'
            
            results[s_id] = {
                'baseline_pass': b_pass,
                'hivemind_pass': h_pass
            }
            if b_pass: baseline_passes += 1
            if h_pass: hivemind_passes += 1
            total += 1
            
    # Read YAMLs
    scenarios_data = []
    for filename in sorted(os.listdir(yaml_dir)):
        if not filename.endswith('.yaml'):
            continue
        with open(os.path.join(yaml_dir, filename), 'r') as f:
            data = yaml.safe_load(f)
            s_id = int(data['id'])
            
            res = results.get(s_id, {'baseline_pass': False, 'hivemind_pass': False})
            
            scenarios_data.append({
                'id': s_id,
                'name': data['name'].replace('_', ' ').title(),
                'tier': data['tier'],
                'baseline_fails_by': data.get('baseline_fails_by', ''),
                'hivemind_mechanism': data.get('hivemind_mechanism', ''),
                'metric': data.get('metric', ''),
                'baseline_pass': res['baseline_pass'],
                'hivemind_pass': res['hivemind_pass']
            })
            
    # Generate HTML
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>HIVEMIND Scenario Lab</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; height: 100vh; }}
        #sidebar {{ width: 300px; background: #2c3e50; color: white; overflow-y: auto; padding: 10px; }}
        #main {{ flex-grow: 1; display: flex; flex-direction: column; background: #ecf0f1; overflow-y: auto; }}
        #header {{ padding: 20px; background: #34495e; color: white; text-align: center; }}
        #content {{ display: flex; flex-grow: 1; padding: 20px; gap: 20px; }}
        .panel {{ flex: 1; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .scenario-btn {{ display: block; width: 100%; padding: 10px; margin-bottom: 5px; background: #34495e; color: white; border: none; text-align: left; cursor: pointer; border-radius: 4px; }}
        .scenario-btn:hover {{ background: #1abc9c; }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        .mock-canvas {{ width: 100%; height: 300px; background: #bdc3c7; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; font-weight: bold; color: #555; }}
    </style>
</head>
<body>
    <div id="sidebar">
        <h2>Scenarios (35)</h2>
        <div id="scenario-list"></div>
    </div>
    <div id="main">
        <div id="header">
            <h1>HIVEMIND Scenario Lab</h1>
            <h3>Summary: HIVEMIND passes {hivemind_passes} of 35 | Baseline passes {baseline_passes} of 35</h3>
        </div>
        <div id="info-bar" style="padding: 20px; background: white; margin: 20px 20px 0 20px; border-radius: 8px;">
            <h2 id="s-title">Select a scenario from the left</h2>
            <p><strong>Metric:</strong> <span id="s-metric"></span></p>
            <p><strong>HIVEMIND Mechanism:</strong> <span id="s-mech"></span></p>
        </div>
        <div id="content">
            <div class="panel">
                <h2>Baseline Run</h2>
                <div class="mock-canvas">FASTSIM REPLAY PLACEHOLDER</div>
                <p><strong>Fails by:</strong> <span id="b-fails"></span></p>
                <p><strong>Status:</strong> <span id="b-status"></span></p>
            </div>
            <div class="panel">
                <h2>HIVEMIND Run</h2>
                <div class="mock-canvas">FASTSIM REPLAY PLACEHOLDER</div>
                <p><strong>Status:</strong> <span id="h-status"></span></p>
            </div>
        </div>
    </div>

    <script>
        const scenarios = {json.dumps(scenarios_data)};
        
        const listDiv = document.getElementById('scenario-list');
        scenarios.forEach(s => {{
            const btn = document.createElement('button');
            btn.className = 'scenario-btn';
            btn.innerHTML = `[${{s.tier}}] S${{s.id}}: ${{s.name}}`;
            btn.onclick = () => loadScenario(s);
            listDiv.appendChild(btn);
        }});
        
        function loadScenario(s) {{
            document.getElementById('s-title').innerText = `Scenario ${{s.id}}: ${{s.name}}`;
            document.getElementById('s-metric').innerText = s.metric;
            document.getElementById('s-mech').innerText = s.hivemind_mechanism;
            
            document.getElementById('b-fails').innerText = s.baseline_fails_by;
            
            const bStat = document.getElementById('b-status');
            bStat.innerText = s.baseline_pass ? "PASS" : "FAIL";
            bStat.className = s.baseline_pass ? "pass" : "fail";
            
            const hStat = document.getElementById('h-status');
            hStat.innerText = s.hivemind_pass ? "PASS" : "FAIL";
            hStat.className = s.hivemind_pass ? "pass" : "fail";
        }}
    </script>
</body>
</html>
"""
    
    with open('scenario_lab.html', 'w') as f:
        f.write(html_template)
    print("Successfully built self-contained Scenario Lab at scenario_lab.html")

if __name__ == '__main__':
    build_lab()
