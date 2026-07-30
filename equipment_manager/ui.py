"""Maya UI construction and rendering for Equipment Manager."""

from typing import Any, Dict, Optional

from .constants import (
    ARROW_BASE_COLOR,
    BOW_ACTIVE_COLOR,
    BOW_BASE_COLOR,
    CHECK_MARK,
    EQUIPMENT_CONFIGS,
    WINDOW_NAME,
)
from .models import EquipmentConfig, EquipmentState, Side


class EquipmentManagerUI:
    """Build and render Maya controls without changing scene rig nodes."""

    def __init__(self, cmds_module: Any, controller: Any) -> None:
        self.cmds = cmds_module
        self.controller = controller
        self.controls: Dict[str, Any] = {}
        self.main_layout = None

    def show(self) -> None:
        """Replace the existing tool window and build one fresh UI tree."""
        if self.cmds.window(WINDOW_NAME, exists=True):
            self.cmds.deleteUI(WINDOW_NAME)
        self.cmds.window(
            WINDOW_NAME,
            title="Weapon Grip [RIGHT]",
            sizeable=True,
            widthHeight=(430, 210),
        )
        self.main_layout = self.cmds.columnLayout(
            adjustableColumn=True, rowSpacing=6
        )
        self._create_equipment_tabs()
        self._create_equipment_hand_controls()
        self._create_equipment_offset_controls()
        self._create_equipment_follow_controls()
        self._create_bow_controls()
        self.cmds.showWindow(WINDOW_NAME)

    def render(
        self,
        state: EquipmentState,
        config: EquipmentConfig,
    ) -> None:
        """Render the supplied state into labels, colors, and visibility."""
        if not self.cmds.window(WINDOW_NAME, exists=True):
            return
        self.cmds.window(
            WINDOW_NAME,
            e=True,
            title="{} [{}]".format(
                config.title,
                state.equipment_side.name
                if state.equipment_side is not None
                else "UNKNOWN",
            ),
        )
        self._render_tabs(state)
        self._render_hand_pair(
            "equipment_left",
            "equipment_right",
            state.equipment_side,
            config.active_color,
            config.base_color,
        )
        self._edit_button("equipment_left_offset", bgc=config.base_color)
        self._edit_button("equipment_right_offset", bgc=config.base_color)
        self._render_follow_pair(
            "equipment_follow_on",
            "equipment_follow_off",
            state.equipment_follow_enabled,
            config.active_color,
            config.base_color,
        )
        self.cmds.columnLayout(
            self.controls["bow_options"],
            e=True,
            visible=state.current_equipment == "Bow",
        )
        self._render_hand_pair(
            "arrow_left",
            "arrow_right",
            state.arrow_side,
            ARROW_BASE_COLOR,
            ARROW_BASE_COLOR,
        )
        self._render_follow_pair(
            "arrow_follow_on",
            "arrow_follow_off",
            state.arrow_follow_enabled,
            ARROW_BASE_COLOR,
            ARROW_BASE_COLOR,
        )
        self._render_follow_pair(
            "string_follow_on",
            "string_follow_off",
            state.string_follow_enabled,
            BOW_ACTIVE_COLOR,
            BOW_BASE_COLOR,
        )

    @staticmethod
    def hand_label(side: Side, selected: bool) -> str:
        prefix = CHECK_MARK if selected else " "
        return "{} {}_HAND".format(prefix, side.value)

    @staticmethod
    def follow_label(enabled: bool, selected: bool) -> str:
        if selected:
            return "{} FOLLOW {}".format(
                CHECK_MARK, "ON" if enabled else "OFF"
            )
        return "ON" if enabled else "OFF"

    def _create_equipment_tabs(self) -> None:
        self.cmds.setParent(self.main_layout)
        form = self.cmds.formLayout(height=28)
        self.controls["tab_sword"] = self.cmds.button(
            label="\U0001F5E1 Sword",
            h=28,
            c=lambda *_: self.controller.select_equipment("Sword"),
        )
        self.controls["tab_shield"] = self.cmds.button(
            label="\U0001F6E1 Shield",
            h=28,
            c=lambda *_: self.controller.select_equipment("Shield"),
        )
        self.controls["tab_bow"] = self.cmds.button(
            label="\U0001F3F9 Bow",
            h=28,
            c=lambda *_: self.controller.select_equipment("Bow"),
        )
        sword = self.controls["tab_sword"]
        shield = self.controls["tab_shield"]
        bow = self.controls["tab_bow"]
        self.cmds.formLayout(
            form,
            e=True,
            attachForm=[
                (sword, "top", 0), (sword, "left", 0),
                (shield, "top", 0), (bow, "top", 0), (bow, "right", 0),
            ],
            attachPosition=[
                (sword, "right", 2, 33),
                (shield, "left", 2, 33),
                (shield, "right", 2, 66),
                (bow, "left", 2, 66),
            ],
        )
        self.cmds.setParent(self.main_layout)
        self.cmds.separator(h=4)

    def _create_equipment_hand_controls(self) -> None:
        self.cmds.setParent(self.main_layout)
        form = self.cmds.formLayout(height=55)
        self.controls["equipment_left"] = self.cmds.button(
            h=55,
            c=lambda *_: self.controller.switch_equipment_hand(Side.LEFT),
        )
        self.controls["equipment_right"] = self.cmds.button(
            h=55,
            c=lambda *_: self.controller.switch_equipment_hand(Side.RIGHT),
        )
        self._attach_two_columns(
            form,
            self.controls["equipment_left"],
            self.controls["equipment_right"],
        )
        self.cmds.setParent(self.main_layout)
        self.cmds.separator(h=6)

    def _create_equipment_offset_controls(self) -> None:
        self.cmds.setParent(self.main_layout)
        form = self.cmds.formLayout(height=24)
        self.controls["equipment_left_offset"] = self.cmds.button(
            label="LEFT OFFSET",
            h=24,
            c=lambda *_: self.controller.save_equipment_offset(Side.LEFT),
        )
        self.controls["equipment_right_offset"] = self.cmds.button(
            label="RIGHT OFFSET",
            h=24,
            c=lambda *_: self.controller.save_equipment_offset(Side.RIGHT),
        )
        self._attach_two_columns(
            form,
            self.controls["equipment_left_offset"],
            self.controls["equipment_right_offset"],
        )
        self.cmds.setParent(self.main_layout)
        self.cmds.separator(h=6)

    def _create_equipment_follow_controls(self) -> None:
        self.cmds.setParent(self.main_layout)
        form = self.cmds.formLayout(height=24)
        self.controls["equipment_follow_off"] = self.cmds.button(
            h=24,
            c=lambda *_: self.controller.set_equipment_follow(False),
        )
        self.controls["equipment_follow_on"] = self.cmds.button(
            h=24,
            c=lambda *_: self.controller.set_equipment_follow(True),
        )
        self._attach_two_columns(
            form,
            self.controls["equipment_follow_off"],
            self.controls["equipment_follow_on"],
        )
        self.cmds.setParent(self.main_layout)
        self.cmds.separator(h=4, style="none")

    def _create_bow_controls(self) -> None:
        self.cmds.setParent(self.main_layout)
        self.controls["bow_options"] = self.cmds.columnLayout(
            adjustableColumn=True, visible=False
        )
        self._create_arrow_controls()
        self._create_string_controls()
        self._create_pose_controls()

    def _create_arrow_controls(self) -> None:
        self.cmds.separator(h=8, style="in")
        self.cmds.text(label="ARROW", align="left")
        hand_form = self.cmds.formLayout(height=55)
        self.controls["arrow_left"] = self.cmds.button(
            h=55, c=lambda *_: self.controller.switch_arrow_hand(Side.LEFT)
        )
        self.controls["arrow_right"] = self.cmds.button(
            h=55, c=lambda *_: self.controller.switch_arrow_hand(Side.RIGHT)
        )
        self._attach_two_columns(
            hand_form,
            self.controls["arrow_left"],
            self.controls["arrow_right"],
        )
        self.cmds.setParent(self.controls["bow_options"])
        self.cmds.separator(h=6)
        offset_form = self.cmds.formLayout(height=24)
        self.controls["arrow_left_offset"] = self.cmds.button(
            label="LEFT OFFSET", h=24,
            c=lambda *_: self.controller.save_arrow_offset(Side.LEFT),
        )
        self.controls["arrow_right_offset"] = self.cmds.button(
            label="RIGHT OFFSET", h=24,
            c=lambda *_: self.controller.save_arrow_offset(Side.RIGHT),
        )
        self._attach_two_columns(
            offset_form,
            self.controls["arrow_left_offset"],
            self.controls["arrow_right_offset"],
        )
        self.cmds.setParent(self.controls["bow_options"])
        self.cmds.separator(h=6)
        follow_form = self.cmds.formLayout(height=24)
        self.controls["arrow_follow_off"] = self.cmds.button(
            h=24, bgc=ARROW_BASE_COLOR,
            c=lambda *_: self.controller.set_arrow_follow(False),
        )
        self.controls["arrow_follow_on"] = self.cmds.button(
            h=24, bgc=ARROW_BASE_COLOR,
            c=lambda *_: self.controller.set_arrow_follow(True),
        )
        self._attach_two_columns(
            follow_form,
            self.controls["arrow_follow_off"],
            self.controls["arrow_follow_on"],
        )

    def _create_string_controls(self) -> None:
        self.cmds.setParent(self.controls["bow_options"])
        self.cmds.separator(h=6)
        self.cmds.text(label="String Follow", align="left")
        follow_form = self.cmds.formLayout(height=24)
        self.controls["string_follow_off"] = self.cmds.button(
            h=24,
            c=lambda *_: self.controller.set_string_follow(False),
        )
        self.controls["string_follow_on"] = self.cmds.button(
            h=24,
            c=lambda *_: self.controller.set_string_follow(True),
        )
        self._attach_two_columns(
            follow_form,
            self.controls["string_follow_off"],
            self.controls["string_follow_on"],
        )

    def _create_pose_controls(self) -> None:
        self.cmds.setParent(self.controls["bow_options"])
        self.cmds.separator(h=12)
        self.cmds.text(label="BOW & ARROW", align="left")
        pose_form = self.cmds.formLayout(height=24)
        self.controls["arrow_allow_save"] = self.cmds.button(
            label="ALLOW SAVE", h=24,
            c=lambda *_: self.controller.save_arrow_pose(),
        )
        self.controls["arrow_reset"] = self.cmds.button(
            label="ARROW RESET", h=24,
            c=lambda *_: self.controller.reset_arrow_pose(),
        )
        self._attach_two_columns(
            pose_form,
            self.controls["arrow_allow_save"],
            self.controls["arrow_reset"],
        )
        self.cmds.setParent(self.controls["bow_options"])
        self.cmds.separator(h=24)
        release_form = self.cmds.formLayout(height=55)
        self.controls["string_release"] = self.cmds.button(
            label="STRING RELEASE", h=55, bgc=BOW_ACTIVE_COLOR,
            c=lambda *_: self.controller.release_string(),
        )
        self.cmds.formLayout(
            release_form,
            e=True,
            attachForm=[
                (self.controls["string_release"], "top", 0),
                (self.controls["string_release"], "left", 0),
                (self.controls["string_release"], "right", 0),
            ],
        )
        self.cmds.setParent("..")

    def _render_tabs(self, state: EquipmentState) -> None:
        for name, key in (
            ("Sword", "tab_sword"),
            ("Shield", "tab_shield"),
            ("Bow", "tab_bow"),
        ):
            config = EQUIPMENT_CONFIGS[name]
            color = (
                config.active_color
                if state.current_equipment == name
                else config.base_color
            )
            self._edit_button(key, bgc=color)

    def _render_hand_pair(
        self,
        left_key: str,
        right_key: str,
        side: Optional[Side],
        active_color: Any,
        base_color: Any,
    ) -> None:
        left_selected = side is Side.LEFT
        right_selected = side is Side.RIGHT
        self._edit_button(
            left_key,
            label=self.hand_label(Side.LEFT, left_selected),
            bgc=active_color if left_selected else base_color,
        )
        self._edit_button(
            right_key,
            label=self.hand_label(Side.RIGHT, right_selected),
            bgc=active_color if right_selected else base_color,
        )

    def _render_follow_pair(
        self,
        on_key: str,
        off_key: str,
        enabled: Optional[bool],
        active_color: Any,
        base_color: Any,
    ) -> None:
        on_selected = enabled is True
        off_selected = enabled is False
        self._edit_button(
            on_key,
            label=self.follow_label(True, on_selected),
            bgc=active_color if on_selected else base_color,
        )
        self._edit_button(
            off_key,
            label=self.follow_label(False, off_selected),
            bgc=active_color if off_selected else base_color,
        )

    def _edit_button(self, key: str, **kwargs: Any) -> None:
        control = self.controls.get(key)
        if control and self.cmds.control(control, exists=True):
            self.cmds.button(control, e=True, **kwargs)

    def _attach_two_columns(self, form: Any, left: Any, right: Any) -> None:
        self.cmds.formLayout(
            form,
            e=True,
            attachForm=[
                (left, "top", 0), (left, "left", 0),
                (right, "top", 0), (right, "right", 0),
            ],
            attachPosition=[
                (left, "right", 2, 50), (right, "left", 2, 50),
            ],
        )
