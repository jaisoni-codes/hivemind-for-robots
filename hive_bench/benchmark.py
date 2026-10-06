import sys
import os
sys.path.append(os.path.abspath('.'))
import time
import matplotlib.pyplot as plt
from scenarios.runner import run_scenario

def run_benchmarks():
    print("=== HIVEMIND Scalability Benchmark ===")
    robot_counts = [4, 8, 16, 32]
    throughputs = [] 
    
    for n in robot_counts:
        print(f"Running benchmark with {n} robots...")
        tasks, coll, duration = run_scenario(seed=100, headless=True, use_shield=True, num_robots=n, target_tasks=n*2)
        
        if duration > 0:
            tpm = (tasks / duration) * 60.0
        else:
            tpm = 0
            
        throughputs.append(tpm)
        print(f"  -> {n} robots: {tpm:.2f} tasks/min, {coll} collisions")
        
    plt.figure(figsize=(8, 5))
    plt.plot(robot_counts, throughputs, marker='o', linestyle='-', color='b')
    plt.title('HIVEMIND Scalability: Throughput vs Swarm Size')
    plt.xlabel('Number of Robots')
    plt.ylabel('System Throughput (Tasks / Min)')
    plt.grid(True)
    plt.savefig('docs/scalability_curve.png')
    print("Saved benchmark plot to docs/scalability_curve.png")

if __name__ == '__main__':
    run_benchmarks()
