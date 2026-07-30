"""Maya scene operations shared by Sword, Shield, and Bow."""

from typing import Any, Mapping, Optional, Sequence, Tuple

from .constants import TRANSFORM_CHANNELS
from .exceptions import EquipmentAttributeError
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
from .models import EquipmentConfig, Side


class EquipmentService:
    """Mutate common equipment nodes without owning UI or selection state.

    Configured controls and constraints are validated before mutation. Missing
    nodes or incompatible weight aliases raise domain errors for the controller
    to report through Maya's warning channel.
    """

    def __init__(self, cmds_module: Any, configs: Mapping[str, EquipmentConfig]):
        self.cmds = cmds_module
        self.configs = configs

    def get_config(self, equipment_name: str) -> EquipmentConfig:
        try:
            return self.configs[equipment_name]
        except KeyError as exc:
            raise ValueError(
                "Unsupported equipment: {}".format(equipment_name)
            ) from exc

    def switch_side(
        self,
        equipment_name: str,
        side: Side,
        follow_enabled: Optional[bool] = None,
    ) -> None:
        """Switch an equipment constraint/space and restore its saved offset."""
        if not isinstance(side, Side):
            raise ValueError("Unsupported side: {!r}".format(side))
        config = self.get_config(equipment_name)
        require_node(self.cmds, config.control)
        require_node(self.cmds, config.constraint)

        if equipment_name == "Bow":
            self._set_space(config, 0 if side is Side.LEFT else 1)
            if follow_enabled is None:
                follow_enabled = self.is_follow_enabled(equipment_name)
            if follow_enabled:
                self._set_constraint_side(config, side)
        elif equipment_name == "Sword":
            require_attribute(self.cmds, config.constraint, "nodeState")
            self.cmds.setAttr(attribute(config.constraint, "nodeState"), 0)
            self._set_space(config, 1 if side is Side.LEFT else 0)
        else:
            self._set_space(config, 0 if side is Side.LEFT else 1)

        self.apply_offset(equipment_name, side)

    def get_current_side(self, equipment_name: str) -> Optional[Side]:
        """Read the active hand without changing the Maya scene."""
        config = self.get_config(equipment_name)
        if not config.space_attribute:
            raise EquipmentAttributeError(
                "No space attribute configured for {}".format(config.name)
            )
        require_attribute(self.cmds, config.control, config.space_attribute)
        value = self.cmds.getAttr(
            attribute(config.control, config.space_attribute)
        )
        if value not in (0, 1):
            raise EquipmentAttributeError(
                "Expected 0 or 1 for {}; found {}".format(
                    attribute(config.control, config.space_attribute), value
                )
            )
        if equipment_name == "Sword":
            return Side.LEFT if value == 1 else Side.RIGHT
        return Side.LEFT if value == 0 else Side.RIGHT

    def get_scene_state(
        self, equipment_name: str
    ) -> Tuple[Optional[Side], bool]:
        """Read current side and Follow state as one scene snapshot."""
        return (
            self.get_current_side(equipment_name),
            self.is_follow_enabled(equipment_name),
        )

    def save_offset(self, equipment_name: str, side: Side) -> None:
        config = self.get_config(equipment_name)
        save_transform_offset(
            self.cmds, config.control, side, TRANSFORM_CHANNELS
        )

    def apply_offset(self, equipment_name: str, side: Side) -> None:
        config = self.get_config(equipment_name)
        apply_transform_offset(
            self.cmds, config.control, side, TRANSFORM_CHANNELS
        )

    def set_follow(
        self,
        equipment_name: str,
        enabled: bool,
        selected_side: Side,
    ) -> None:
        config = self.get_config(equipment_name)
        require_node(self.cmds, config.constraint)
        if equipment_name == "Bow":
            if enabled:
                self._set_constraint_side(config, selected_side)
            else:
                for alias in self._constraint_aliases(config.constraint):
                    self.cmds.setAttr(attribute(config.constraint, alias), 0)
        else:
            require_attribute(self.cmds, config.constraint, "nodeState")
            self.cmds.setAttr(
                attribute(config.constraint, "nodeState"),
                0 if enabled else 1,
            )

    def is_follow_enabled(self, equipment_name: str) -> bool:
        config = self.get_config(equipment_name)
        require_node(self.cmds, config.constraint)
        if equipment_name == "Bow":
            _side, enabled = read_constraint_side(
                self.cmds, config.constraint
            )
            return enabled
        require_attribute(self.cmds, config.constraint, "nodeState")
        return self.cmds.getAttr(
            attribute(config.constraint, "nodeState")
        ) == 0

    def _constraint_aliases(self, constraint: str) -> Sequence[str]:
        aliases = self.cmds.parentConstraint(constraint, q=True, wal=True) or []
        resolve_side_aliases(aliases)
        return aliases

    def _set_constraint_side(
        self,
        config: EquipmentConfig,
        side: Side,
    ) -> None:
        require_attribute(self.cmds, config.constraint, "nodeState")
        self.cmds.setAttr(attribute(config.constraint, "nodeState"), 0)
        left_alias, right_alias = resolve_side_aliases(
            self._constraint_aliases(config.constraint)
        )
        left_weight, right_weight = side_weights(side)
        self.cmds.setAttr(
            attribute(config.constraint, left_alias), left_weight
        )
        self.cmds.setAttr(
            attribute(config.constraint, right_alias), right_weight
        )

    def _set_space(self, config: EquipmentConfig, value: int) -> None:
        if not config.space_attribute:
            raise EquipmentAttributeError(
                "No space attribute configured for {}".format(config.name)
            )
        require_attribute(self.cmds, config.control, config.space_attribute)
        self.cmds.setAttr(
            attribute(config.control, config.space_attribute), value
        )
