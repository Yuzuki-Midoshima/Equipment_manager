"""Small Maya command helpers shared by scene services."""

from typing import Any, Iterable, Optional, Sequence, Tuple

from .exceptions import (
    ConstraintAliasError,
    ConstraintStateError,
    EquipmentAttributeError,
    EquipmentNodeError,
)
from .models import Side


MayaCommands = Any


def attribute(node: str, name: str) -> str:
    return "{}.{}".format(node, name)


def require_node(cmds: MayaCommands, node: str) -> None:
    """Raise a user-facing domain error when a configured node is absent."""
    if not cmds.objExists(node):
        raise EquipmentNodeError(
            "Required Maya node was not found: {}".format(node)
        )


def require_attribute(cmds: MayaCommands, node: str, name: str) -> None:
    """Raise a domain error when a required attribute is absent."""
    require_node(cmds, node)
    if not cmds.attributeQuery(name, node=node, exists=True):
        raise EquipmentAttributeError(
            "Required Maya attribute was not found: {}".format(
                attribute(node, name)
            )
        )


def resolve_side_aliases(aliases: Sequence[str]) -> Tuple[str, str]:
    """Return unambiguous left/right weight aliases."""
    left = [alias for alias in aliases if alias.startswith("L_")]
    right = [alias for alias in aliases if alias.startswith("R_")]
    if len(left) != 1 or len(right) != 1:
        raise ConstraintAliasError(
            "Expected one L_ and one R_ constraint weight; found: {}".format(
                ", ".join(aliases) or "none"
            )
        )
    return left[0], right[0]


def side_weights(side: Side) -> Tuple[int, int]:
    """Return left/right numeric weights for the selected side."""
    if not isinstance(side, Side):
        raise ValueError("Unsupported side: {!r}".format(side))
    return int(side is Side.LEFT), int(side is Side.RIGHT)


def read_constraint_side(
    cmds: MayaCommands,
    constraint: str,
    tolerance: float = 0.001,
) -> Tuple[Optional[Side], bool]:
    """Read side/follow state from dynamic parent-constraint aliases.

    Zero weights mean Follow OFF and no observable side. Simultaneously active
    left and right weights are rejected because the UI cannot represent them.
    """
    require_node(cmds, constraint)
    aliases = cmds.parentConstraint(constraint, q=True, wal=True) or []
    left_alias, right_alias = resolve_side_aliases(aliases)
    left_active = cmds.getAttr(attribute(constraint, left_alias)) > tolerance
    right_active = cmds.getAttr(attribute(constraint, right_alias)) > tolerance
    if left_active and right_active:
        raise ConstraintStateError(
            "Both left and right weights are active: {}".format(constraint)
        )
    if left_active:
        return Side.LEFT, True
    if right_active:
        return Side.RIGHT, True
    return None, False


def ensure_transform_attributes(
    cmds: MayaCommands,
    control: str,
    channels: Iterable[str],
) -> None:
    require_node(cmds, control)
    for side in Side:
        for channel in channels:
            name = "{}Grip_{}".format(side.value, channel)
            if not cmds.attributeQuery(name, node=control, exists=True):
                cmds.addAttr(control, ln=name, at="double")


def save_transform_offset(
    cmds: MayaCommands,
    control: str,
    side: Side,
    channels: Iterable[str],
) -> None:
    ensure_transform_attributes(cmds, control, channels)
    for channel in channels:
        cmds.setAttr(
            attribute(control, "{}Grip_{}".format(side.value, channel)),
            cmds.getAttr(attribute(control, channel)),
        )


def apply_transform_offset(
    cmds: MayaCommands,
    control: str,
    side: Side,
    channels: Iterable[str],
) -> None:
    ensure_transform_attributes(cmds, control, channels)
    for channel in channels:
        cmds.setAttr(
            attribute(control, channel),
            cmds.getAttr(
                attribute(control, "{}Grip_{}".format(side.value, channel))
            ),
        )
