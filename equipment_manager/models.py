"""Typed configuration and runtime state for Equipment Manager."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


Color = Tuple[float, float, float]


class Side(str, Enum):
    """Supported rig sides and their scene-name prefixes."""

    LEFT = "L"
    RIGHT = "R"


@dataclass(frozen=True)
class EquipmentConfig:
    """Rig nodes and UI presentation for one equipment type."""

    name: str
    control: str
    constraint: str
    space_attribute: Optional[str]
    title: str
    active_color: Color
    base_color: Color


@dataclass(frozen=True)
class ArrowConfig:
    """Scene contract for Arrow operations."""

    control: str
    constraint: str
    body: str
    reset_reference: str


@dataclass(frozen=True)
class StringConfig:
    """Scene contract for bow-string operations."""

    control: str
    draw_attributes: Tuple[str, ...]
    translate_attributes: Tuple[str, ...]
    fk_match_pairs: Tuple[Tuple[str, str], ...]
    ik_shoulder_joint: str
    ik_elbow_joint: str
    ik_wrist_joint: str
    ik_hand_control: str
    ik_pole_control: str


@dataclass
class EquipmentState:
    """Single source of truth for all user-selectable tool state."""

    current_equipment: str = "Sword"
    equipment_side: Optional[Side] = None
    equipment_follow_enabled: Optional[bool] = None
    arrow_side: Optional[Side] = None
    arrow_follow_enabled: Optional[bool] = None
    string_follow_enabled: Optional[bool] = None
