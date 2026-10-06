from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import time

@dataclass
class Pose2D:
    x: float
    y: float
    theta: float
    covariance: float = 0.01
    match_score: float = 1.0

@dataclass
class ScanFrame:
    robot_id: str
    pose: Pose2D
    ranges: List[float]
    angles: List[float]
    timestamp: float = field(default_factory=time.time)

@dataclass
class Detection:
    label: str
    range: float
    bearing: float
    confidence: float
    x: float = 0.0
    y: float = 0.0
    timestamp: float = field(default_factory=time.time)
    seq_num: int = 0  # Added for A6 (buffering)

@dataclass
class ObjectRecord:
    id: str
    label: str
    pose: Pose2D
    confidence: float
    first_seen: float
    last_seen: float
    seen_count: int
    state: str 
    history: List[Tuple[Pose2D, float]]
    observed_by: List[str]
    is_dynamic: bool

@dataclass
class Task:
    id: str
    type: str  
    priority: int
    target_pose: Optional[Pose2D] = None
    target_label: Optional[str] = None
    assigned_robot: Optional[str] = None
    timestamp: float = field(default_factory=time.time) # Added for A6
    ttl: float = 5.0 # Added for A6 (Time to live in seconds)

@dataclass
class RobotStatus:
    id: str
    pose: Pose2D
    velocity: Tuple[float, float]
    current_task_id: Optional[str]
    state: str
    loc_state: str = "OK" 
    comms_state: str = "CONNECTED" # Added for A6 (CONNECTED, DEGRADED, DISCONNECTED, SAFE)
    timestamp: float = field(default_factory=time.time)

@dataclass
class Event:
    type: str
    payload: Dict
    timestamp: float = field(default_factory=time.time)
    seq_num: int = 0
