"""Bow, Arrow, and String-specific Maya scene operations."""

import math
from typing import Any, Optional, Sequence, Tuple

from .constants import TRANSFORM_CHANNELS
from .maya_utils import (
    apply_transform_offset,
    attribute,
    read_constraint_side,
    require_attribute,
    require_node,
    resolve_side_aliases,
    save_transform_offset,
    side_weights,
)
from .models import ArrowConfig, Side, StringConfig


class BowService:
    """Mutate Arrow and String nodes defined by the rig configuration."""

    def __init__(
        self,
        cmds_module: Any,
        arrow_config: ArrowConfig,
        string_config: StringConfig,
    ) -> None:
        self.cmds = cmds_module
        self.arrow = arrow_config
        self.string = string_config

    def switch_arrow_side(
        self, side: Side, follow_enabled: Optional[bool]
    ) -> None:
        self.apply_arrow_offset(side)
        if follow_enabled:
            self.set_arrow_follow(True, side)

    def set_arrow_follow(self, enabled: bool, side: Side) -> None:
        require_node(self.cmds, self.arrow.constraint)
        aliases = self._arrow_aliases()
        if enabled:
            left_alias, right_alias = resolve_side_aliases(aliases)
            left_weight, right_weight = side_weights(side)
            self.cmds.setAttr(
                attribute(self.arrow.constraint, left_alias), left_weight
            )
            self.cmds.setAttr(
                attribute(self.arrow.constraint, right_alias), right_weight
            )
        else:
            for alias in aliases:
                self.cmds.setAttr(attribute(self.arrow.constraint, alias), 0)

    def get_arrow_scene_state(self) -> Tuple[Optional[Side], bool]:
        """Read Arrow side and Follow state from its constraint weights."""
        return read_constraint_side(self.cmds, self.arrow.constraint)

    def save_arrow_offset(self, side: Side) -> None:
        save_transform_offset(
            self.cmds, self.arrow.control, side, TRANSFORM_CHANNELS
        )

    def apply_arrow_offset(self, side: Side) -> None:
        apply_transform_offset(
            self.cmds, self.arrow.control, side, TRANSFORM_CHANNELS
        )

    def save_arrow_pose(self) -> None:
        """Save the Arrow body position into the String reset reference."""
        require_node(self.cmds, self.arrow.body)
        require_node(self.cmds, self.arrow.reset_reference)
        matrix = self.cmds.xform(
            self.arrow.body, q=True, ws=True, matrix=True
        )
        self.cmds.xform(
            self.arrow.reset_reference, ws=True, matrix=matrix
        )

    def reset_arrow_pose(self) -> None:
        """Snap Arrow_LOC once to String_Reset_LOC without reparenting."""
        require_node(self.cmds, self.arrow.body)
        require_node(self.cmds, self.arrow.reset_reference)
        matrix = self.cmds.xform(
            self.arrow.reset_reference, q=True, ws=True, matrix=True
        )
        self.cmds.xform(self.arrow.body, ws=True, matrix=matrix)
        self.cmds.refresh(force=True)

    def release_string(self) -> None:
        require_node(self.cmds, self.string.control)
        for name in self.string.draw_attributes:
            if self.cmds.attributeQuery(
                name, node=self.string.control, exists=True
            ):
                self.cmds.setAttr(attribute(self.string.control, name), 0)
        for name in self.string.translate_attributes:
            plug = attribute(self.string.control, name)
            if not self.cmds.connectionInfo(plug, isDestination=True):
                self.cmds.setAttr(plug, 0)

    def set_string_follow(self, enabled: bool, bow_side: Side) -> None:
        if not isinstance(bow_side, Side):
            raise ValueError(
                "Bow side is unknown; select a Bow hand before String Follow"
            )
        arm = "R" if bow_side is Side.LEFT else "L"
        settings = "{}_arm_settings_anim".format(arm)
        hand = "Ik_{}_hand_anim".format(arm)
        require_node(self.cmds, settings)
        require_attribute(self.cmds, settings, "FKIK")
        if enabled:
            self._match_ik_controls_to_joints(arm, settings)
            require_node(self.cmds, hand)
            require_node(self.cmds, self.string.control)
            self.cmds.select(hand, self.string.control, r=True)
            self.cmds.setToolTo("Move")
        else:
            self._match_fk_controls_to_joints(arm)
            self.cmds.setAttr(attribute(settings, "FKIK"), 0)
            self.cmds.select(clear=True)

    def get_string_follow_enabled(
        self, bow_side: Optional[Side]
    ) -> Optional[bool]:
        """Read the opposite arm FKIK value used by String Follow."""
        if bow_side is None:
            return None
        arm = "R" if bow_side is Side.LEFT else "L"
        settings = "{}_arm_settings_anim".format(arm)
        require_attribute(self.cmds, settings, "FKIK")
        return bool(self.cmds.getAttr(attribute(settings, "FKIK")))

    def _match_fk_controls_to_joints(self, arm: str) -> None:
        """Match shoulder, elbow, and wrist FK controls before FKIK changes."""
        for joint_template, control_template in self.string.fk_match_pairs:
            joint = joint_template.format(side=arm)
            control = control_template.format(side=arm)
            require_node(self.cmds, joint)
            require_node(self.cmds, control)
            matrix = self.cmds.xform(joint, q=True, ws=True, matrix=True)
            self.cmds.xform(control, ws=True, matrix=matrix)

    def _match_ik_controls_to_joints(
        self, arm: str, settings: str
    ) -> None:
        """Match IK hand and pole controls to the current FK-driven pose."""
        names = {
            "shoulder": self.string.ik_shoulder_joint.format(side=arm),
            "elbow": self.string.ik_elbow_joint.format(side=arm),
            "wrist": self.string.ik_wrist_joint.format(side=arm),
            "hand": self.string.ik_hand_control.format(side=arm),
            "pole": self.string.ik_pole_control.format(side=arm),
        }
        for node in names.values():
            require_node(self.cmds, node)

        shoulder = self._world_position(names["shoulder"])
        elbow = self._world_position(names["elbow"])
        wrist = self._world_position(names["wrist"])
        pole_position = self._calculate_pole_position(
            shoulder,
            elbow,
            wrist,
        )

        self.cmds.matchTransform(
            names["hand"], names["wrist"], pos=True, rot=True
        )
        self.cmds.xform(names["pole"], ws=True, t=pole_position)
        self.cmds.setAttr(attribute(settings, "FKIK"), 1)

    def _world_position(self, node: str) -> Tuple[float, float, float]:
        values = self.cmds.xform(node, q=True, ws=True, t=True)
        return float(values[0]), float(values[1]), float(values[2])

    @classmethod
    def _calculate_pole_position(
        cls,
        shoulder: Tuple[float, float, float],
        elbow: Tuple[float, float, float],
        wrist: Tuple[float, float, float],
    ) -> Tuple[float, float, float]:
        """Calculate a pole position that remains on the current arm plane."""
        arm_axis = cls._subtract(wrist, shoulder)
        axis_length_sq = cls._dot(arm_axis, arm_axis)
        if axis_length_sq < 1.0e-10:
            raise ValueError("Shoulder and wrist positions overlap")

        shoulder_to_elbow = cls._subtract(elbow, shoulder)
        projection_scale = (
            cls._dot(shoulder_to_elbow, arm_axis) / axis_length_sq
        )
        projection = cls._add(
            shoulder, cls._scale(arm_axis, projection_scale)
        )
        direction = cls._subtract(elbow, projection)
        if cls._length(direction) < 1.0e-5:
            raise ValueError(
                "Cannot calculate pole vector from a straight arm"
            )
        distance = cls._length(shoulder_to_elbow) + cls._length(
            cls._subtract(wrist, elbow)
        )
        pole = cls._add(elbow, cls._scale(cls._normalize(direction), distance))
        return pole

    @staticmethod
    def _add(left, right):
        return tuple(left[index] + right[index] for index in range(3))

    @staticmethod
    def _subtract(left, right):
        return tuple(left[index] - right[index] for index in range(3))

    @staticmethod
    def _scale(vector, scalar):
        return tuple(value * scalar for value in vector)

    @staticmethod
    def _dot(left, right):
        return sum(left[index] * right[index] for index in range(3))

    @classmethod
    def _length(cls, vector):
        return math.sqrt(cls._dot(vector, vector))

    @classmethod
    def _normalize(cls, vector):
        length = cls._length(vector)
        return cls._scale(vector, 1.0 / length)

    def _arrow_aliases(self) -> Sequence[str]:
        aliases = self.cmds.parentConstraint(
            self.arrow.constraint, q=True, wal=True
        ) or []
        resolve_side_aliases(aliases)
        return aliases
