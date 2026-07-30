"""Stable Maya entry point for Equipment Manager."""

from typing import Optional

import maya.cmds as cmds

from equipment_manager import EquipmentManagerApp


_app: Optional[EquipmentManagerApp] = None


def show() -> EquipmentManagerApp:
    """Create and show a fresh Equipment Manager application instance."""
    global _app
    _app = EquipmentManagerApp(cmds).show()
    return _app
