"""Application state and UI event coordination."""

from typing import Any, Callable, Optional

from .exceptions import EquipmentManagerError
from .models import EquipmentState, Side


class EquipmentController:
    """Coordinate UI events, state transitions, and scene services.

    ``EquipmentState`` is the only source of user-selectable state. Scene
    mutations are delegated to services and UI rendering is delegated to the
    attached UI instance.
    """

    def __init__(
        self,
        cmds_module: Any,
        equipment_service: Any,
        bow_service: Any,
        state: Optional[EquipmentState] = None,
    ) -> None:
        self.cmds = cmds_module
        self.equipment_service = equipment_service
        self.bow_service = bow_service
        self.state = state or EquipmentState()
        self.ui = None

    def attach_ui(self, ui: Any) -> None:
        self.ui = ui

    def select_equipment(self, equipment_name: str) -> None:
        def operation() -> None:
            self.equipment_service.get_config(equipment_name)
            self.state.current_equipment = equipment_name
            self._sync_component(self._sync_equipment_state)
            if equipment_name == "Bow":
                self._sync_component(
                    lambda: self._sync_string_state(
                        self.state.equipment_side
                    )
                )
            self._refresh_ui()

        self._run_safely(operation)

    def sync_state_from_scene(self) -> None:
        """Read scene state without calling any mutating Maya command."""
        self._sync_component(self._sync_equipment_state)
        self._sync_component(self._sync_arrow_state)

        if self.state.current_equipment == "Bow":
            self._sync_component(
                lambda: self._sync_string_state(
                    self.state.equipment_side
                )
            )
        else:
            self._sync_component(self._sync_string_from_bow_scene)

    def switch_equipment_hand(self, side: Side, announce: bool = True) -> None:
        def operation() -> None:
            self.equipment_service.switch_side(
                self.state.current_equipment,
                side,
                self.state.equipment_follow_enabled,
            )
            self.state.equipment_side = side
            self.state.equipment_follow_enabled = (
                self.equipment_service.is_follow_enabled(
                    self.state.current_equipment
                )
            )
            self.cmds.refresh(force=True)
            self._refresh_ui()
            if announce:
                self._show_status(
                    "{} {}".format(
                        self.state.current_equipment.upper(), side.name
                    )
                )

        self._run_safely(operation)

    def save_equipment_offset(self, side: Side) -> None:
        def operation() -> None:
            self.equipment_service.save_offset(
                self.state.current_equipment, side
            )
            self._show_status(
                "{} {} OFFSET SAVED".format(
                    self.state.current_equipment.upper(), side.name
                )
            )

        self._run_safely(operation)

    def set_equipment_follow(self, enabled: bool) -> None:
        def operation() -> None:
            self.equipment_service.set_follow(
                self.state.current_equipment,
                enabled,
                self.state.equipment_side,
            )
            self.state.equipment_follow_enabled = enabled
            self.cmds.refresh(force=True)
            self._refresh_ui()
            self._show_status("FOLLOW {}".format("ON" if enabled else "OFF"))

        self._run_safely(operation)

    def switch_arrow_hand(self, side: Side) -> None:
        def operation() -> None:
            self.bow_service.switch_arrow_side(
                side, self.state.arrow_follow_enabled
            )
            self.state.arrow_side = side
            self._refresh_ui()
            self._show_status("ARROW {}".format(side.name))

        self._run_safely(operation)

    def set_arrow_follow(self, enabled: bool) -> None:
        def operation() -> None:
            self.bow_service.set_arrow_follow(
                enabled, self.state.arrow_side
            )
            self.state.arrow_follow_enabled = enabled
            self._refresh_ui()
            self._show_status(
                "ARROW FOLLOW {}".format("ON" if enabled else "OFF")
            )

        self._run_safely(operation)

    def save_arrow_offset(self, side: Side) -> None:
        self._run_safely(
            lambda: self._save_arrow_offset_and_notify(side)
        )

    def save_arrow_pose(self) -> None:
        self._run_safely(
            lambda: self._execute_and_notify(
                self.bow_service.save_arrow_pose, "ARROW POSE SAVED"
            )
        )

    def reset_arrow_pose(self) -> None:
        self._run_safely(
            lambda: self._execute_and_notify(
                self.bow_service.reset_arrow_pose, "ARROW RESET"
            )
        )

    def release_string(self) -> None:
        self._run_safely(
            lambda: self._execute_and_notify(
                self.bow_service.release_string, "STRING RELEASED"
            )
        )

    def set_string_follow(self, enabled: bool) -> None:
        def operation() -> None:
            self.bow_service.set_string_follow(
                enabled, self.state.equipment_side
            )
            self.state.string_follow_enabled = enabled
            self._refresh_ui()
            self._show_status(
                "STRING FOLLOW {}".format("ON" if enabled else "OFF")
            )

        self._run_safely(operation)

    def refresh(self) -> None:
        """Render current state without mutating scene nodes."""
        self._refresh_ui()

    def current_config(self) -> Any:
        return self.equipment_service.get_config(
            self.state.current_equipment
        )

    def _save_arrow_offset_and_notify(self, side: Side) -> None:
        self.bow_service.save_arrow_offset(side)
        self._show_status("ARROW {} OFFSET SAVED".format(side.name))

    def _execute_and_notify(
        self, operation: Callable[[], None], message: str
    ) -> None:
        operation()
        self._show_status(message)

    def _sync_equipment_state(self) -> None:
        self.state.equipment_side = None
        self.state.equipment_follow_enabled = None
        side, follow_enabled = self.equipment_service.get_scene_state(
            self.state.current_equipment
        )
        self.state.equipment_side = side
        self.state.equipment_follow_enabled = follow_enabled

    def _sync_arrow_state(self) -> None:
        self.state.arrow_side = None
        self.state.arrow_follow_enabled = None
        side, follow_enabled = self.bow_service.get_arrow_scene_state()
        self.state.arrow_side = side
        self.state.arrow_follow_enabled = follow_enabled

    def _sync_string_state(self, bow_side: Optional[Side]) -> None:
        self.state.string_follow_enabled = None
        self.state.string_follow_enabled = (
            self.bow_service.get_string_follow_enabled(bow_side)
        )

    def _read_bow_side(self) -> Optional[Side]:
        return self.equipment_service.get_current_side("Bow")

    def _sync_string_from_bow_scene(self) -> None:
        self._sync_string_state(self._read_bow_side())

    def _sync_component(self, operation: Callable[[], None]) -> None:
        try:
            operation()
        except (EquipmentManagerError, ValueError, RuntimeError) as exc:
            self.cmds.warning("Equipment Manager: {}".format(exc))

    def _run_safely(self, operation: Callable[[], None]) -> None:
        try:
            operation()
        except (EquipmentManagerError, ValueError, RuntimeError) as exc:
            self.cmds.warning("Equipment Manager: {}".format(exc))
            self._show_status("ERROR: {}".format(exc))

    def _refresh_ui(self) -> None:
        if self.ui is not None:
            self.ui.render(self.state, self.current_config())

    def _show_status(self, message: str) -> None:
        self.cmds.inViewMessage(
            amg="<hl>{}</hl>".format(message),
            pos="midCenter",
            fade=True,
        )
