from typing import Protocol
from enum import Enum

class ActivityType(Enum):
    TASK = "TASK"
    GOAL = "GOAL"
    HABIT = "HABIT"
    COURSE = "COURSE"
    WORKOUT = "WORKOUT"

class ActivityInterface(Protocol):
    """
    Any domain model (Task, Habit, Course) that can be executed must implement this interface 
    to provide the runtime with necessary metadata without leaking internal schemas.
    """
    def get_runtime_identity(self) -> str: ...
    def get_entity_type(self) -> ActivityType: ...
    def get_planned_duration(self) -> int: ... # seconds
    def can_be_executed(self) -> bool: ...
