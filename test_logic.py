import math, random, heapq

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
        ox, oy = round(obs[0]), round(obs[1])
        blocked.update([(ox, oy), (ox+1, oy), (ox-1, oy), (ox, oy+1), (ox, oy-1)])
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

class IntelligentRobot:
    def __init__(self, r_id, x, y):
        self.id = r_id
        self.x = x; self.y = y; self.theta = 0
        self.v = 0; self.w = 0
        self.path = []
        self.target = None
        self.memory_obstacles = []
        self.state = 'IDLE'
    def replan(self):
        if not self.target: return
        self.path = a_star_search((self.x, self.y), self.target, self.memory_obstacles)

    def update(self, dt, all_robots, humans, truth_dict, central_memory):
        new_memory = []
        for obj_id, obj in truth_dict.items():
            dist = math.hypot(obj['pose'][0] - self.x, obj['pose'][1] - self.y)
            if dist < 4.0:
                new_memory.append((obj['pose'][0], obj['pose'][1]))
        if len(new_memory) != len(self.memory_obstacles):
            self.memory_obstacles = new_memory
            self.replan()

        if self.target is None or len(self.path) == 0:
            for _ in range(10):
                self.target = (random.uniform(2, 18), random.uniform(2, 18))
                self.replan()
                if len(self.path) > 0: break
            self.state = 'MOVING'

        safe_to_move = True
        for other in all_robots:
            if other.id != self.id:
                if math.hypot(other.x - self.x, other.y - self.y) < 1.5:
                    if self.id > other.id: safe_to_move = False
        
        if not safe_to_move:
            self.v = 0; self.w = 0; self.state = 'YIELDING'
            return
        
        self.state = 'MOVING'

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
                if abs(angle_diff) < 0.5: self.v = 1.2
                else: self.v = 0.0
        else:
            self.v = 0; self.w = 0
        self.theta += self.w * dt
        self.theta = (self.theta + math.pi) % (2 * math.pi) - math.pi
        self.x += self.v * math.cos(self.theta) * dt
        self.y += self.v * math.sin(self.theta) * dt

r = IntelligentRobot('AGV-1', 2, 2)
truth = {}
for x in [6, 14]:
    for y in [5, 6, 7, 8, 12, 13, 14, 15]:
        truth[f"rack_{x}_{y}"] = {"class": "shelf", "pose": [x, y, 0]}

print("Tick 1")
r.update(0.1, [r], [], truth, {})
print("Path:", r.path)
print("Target:", r.target)
print("V:", r.v, "W:", r.w, "X:", r.x, "Y:", r.y)

print("Tick 2")
r.update(0.1, [r], [], truth, {})
print("V:", r.v, "W:", r.w, "X:", r.x, "Y:", r.y)

