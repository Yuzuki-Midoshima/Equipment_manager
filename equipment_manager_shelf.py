"""Equipment Manager shelf command for Maya 2026."""

import importlib
import sys
from pathlib import Path

import maya.cmds as cmds


TOOL_DIRECTORY_NAME = "Equipment_manager"
ENTRY_MODULE_NAME = "launch_equipment_manager"


def resolve_tool_directory() -> Path:
    """Resolve the tool relative to Maya's locale-independent user root."""
    tool_directory = (
        Path(cmds.internalVar(userAppDir=True))
        / "scripts"
        / TOOL_DIRECTORY_NAME
    )
    if not tool_directory.is_dir():
        raise RuntimeError(
            "Equipment Manager folder was not found: {}".format(
                tool_directory
            )
        )
    return tool_directory


def unload_tool_modules() -> None:
    """Unload only Equipment Manager modules for development-time reloads."""
    module_names = tuple(sys.modules)
    for module_name in module_names:
        if (
            module_name == ENTRY_MODULE_NAME
            or module_name == "equipment_manager"
            or module_name.startswith("equipment_manager.")
        ):
            del sys.modules[module_name]
    importlib.invalidate_caches()


def launch() -> None:
    """Load the current source files and display one manager window."""
    tool_directory = str(resolve_tool_directory())
    if tool_directory not in sys.path:
        sys.path.insert(0, tool_directory)

    unload_tool_modules()
    entry_module = importlib.import_module(ENTRY_MODULE_NAME)
    entry_module.show()


launch()
