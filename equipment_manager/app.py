"""Composition root for Equipment Manager."""

from typing import Any

from .bow_service import BowService
from .constants import ARROW_CONFIG, EQUIPMENT_CONFIGS, STRING_CONFIG
from .controller import EquipmentController
from .models import EquipmentState
from .services import EquipmentService
from .ui import EquipmentManagerUI


class EquipmentManagerApp:
    """Assemble and display the tool using an injected ``maya.cmds`` module.

    The app owns object lifetimes only. Scene behavior belongs to services,
    interaction state to the controller, and Maya controls to the UI class.
    """

    def __init__(self, cmds_module: Any) -> None:
        self.cmds = cmds_module
        self.state = EquipmentState()
        self.equipment_service = EquipmentService(
            cmds_module, EQUIPMENT_CONFIGS
        )
        self.bow_service = BowService(
            cmds_module, ARROW_CONFIG, STRING_CONFIG
        )
        self.controller = EquipmentController(
            cmds_module,
            self.equipment_service,
            self.bow_service,
            self.state,
        )
        self.ui = EquipmentManagerUI(cmds_module, self.controller)
        self.controller.attach_ui(self.ui)

    def show(self) -> "EquipmentManagerApp":
        """Build one window and render a read-only snapshot of the scene."""
        self.ui.show()
        self.controller.sync_state_from_scene()
        self.controller.refresh()
        return self
