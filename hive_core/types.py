from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import time

@dataclass
class Pose2D:
    x: float
    y: float
    theta: float

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
    timestamp: float = field(default_factory=time.time)

@dataclass
class ObjectRecord:
    id: str
    label: str
    pose: Pose2D
    confidence: float
    first_seen: float
    last_seen: float
    seen_count: int
    state: str  # ACTIVE, STALE, MOVED, GONE
    history: List[Tuple[Pose2D, float]]
    observed_by: List[str]
    is_dynamic: bool

@dataclass
class Task:
    id: str
    type: str  # GOTO_OBJECT, INSPECT, EXPLORE, VERIFY, REFRESH, RETURN_TO_DOCK
    priority: int
    target_pose: Optional[Pose2D] = None
    target_label: Optional[str] = None
    assigned_robot: Optional[str] = None

@dataclass
class RobotStatus:
    id: str
    pose: Pose2D
    velocity: Tuple[float, float]  # linear, angular
    current_task_id: Optional[str]
    state: str  # IDLE, MOVING, BLOCKED, CHARGING
    timestamp: float = field(default_factory=time.time)

