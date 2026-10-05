import numpy as np
import math
import heapq
from typing import List, Tuple, Optional

class OccupancyGrid:
    def __init__(self, width_m: float, height_m: float, resolution: float = 0.1):
        self.resolution = resolution
        self.width_cells = int(width_m / resolution)
        self.height_cells = int(height_m / resolution)
        # Log-odds grid: 0 is unknown, >0 is occupied, <0 is free
        self.grid = np.zeros((self.width_cells, self.height_cells), dtype=np.float32)
    
    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        gx = int(x / self.resolution)
        gy = int(y / self.resolution)
        return max(0, min(self.width_cells - 1, gx)), max(0, min(self.height_cells - 1, gy))
    
    def grid_to_world(self, gx: int, gy: int) -> Tuple[float, float]:
        return (gx + 0.5) * self.resolution, (gy + 0.5) * self.resolution
        
    def is_free(self, gx: int, gy: int) -> bool:
        if 0 <= gx < self.width_cells and 0 <= gy < self.height_cells:
            return self.grid[gx, gy] <= 0 # Unknown or free treated as passable for basic A*
        return False

def a_star(grid: OccupancyGrid, start: Tuple[float, float], goal: Tuple[float, float]) -> List[Tuple[float, float]]:
    sgx, sgy = grid.world_to_grid(*start)
    ggx, ggy = grid.world_to_grid(*goal)
    
    if not grid.is_free(ggx, ggy):
        return []
        
    open_set = []
    heapq.heappush(open_set, (0, sgx, sgy))
    came_from = {}
    g_score = {(sgx, sgy): 0}
    
    while open_set:
        _, cx, cy = heapq.heappop(open_set)
        
        if (cx, cy) == (ggx, ggy):
            path = []
            curr = (cx, cy)
            while curr in came_from:
                path.append(grid.grid_to_world(curr[0], curr[1]))
                curr = came_from[curr]
            path.append(grid.grid_to_world(sgx, sgy))
            return path[::-1]
            
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
            nx, ny = cx + dx, cy + dy
            if grid.is_free(nx, ny):
                cost = math.hypot(dx, dy)
                tentative_g = g_score[(cx, cy)] + cost
                if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                    came_from[(nx, ny)] = (cx, cy)
                    g_score[(nx, ny)] = tentative_g
                    f_score = tentative_g + math.hypot(ggx - nx, ggy - ny)
                    heapq.heappush(open_set, (f_score, nx, ny))
    return []
