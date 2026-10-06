import time, math
import mem_app

sim = mem_app.RealSimulator()
for i in range(1000):
    sim.step(0.04)
    if i % 100 == 0:
        print(f"Tick {i}")
        for r in sim.robots:
            print(f"{r.id} - x:{r.x:.2f} y:{r.y:.2f} state:{r.state} path_len:{len(r.path)} v:{r.v:.2f}")
