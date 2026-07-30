"""Maya-independent behavior tests using lightweight ``cmds`` fakes."""

import math
import unittest

from equipment_manager.app import EquipmentManagerApp
from equipment_manager.bow_service import BowService
from equipment_manager.constants import (
    ARROW_CONFIG,
    EQUIPMENT_CONFIGS,
    STRING_CONFIG,
)
from equipment_manager.controller import EquipmentController
from equipment_manager.exceptions import (
    ConstraintStateError,
    EquipmentAttributeError,
)
from equipment_manager.maya_utils import (
    resolve_side_aliases,
    side_weights,
)
from equipment_manager.models import EquipmentState, Side
from equipment_manager.services import EquipmentService
from equipment_manager.ui import EquipmentManagerUI


class FakeSceneCmds:
    """Read-capable scene fake that records every mutation request."""

    def __init__(self):
        self.messages = []
        self.set_attr_calls = []
        self.xform_calls = []
        self.match_transform_calls = []
        self.nodes = {
            "Sword_CTRL",
            "Sword_Follow_GRP_parentConstraint1",
            "Shield_CTRL",
            "Shield_Follow_GRP_parentConstraint1",
            "ALL_Bow_anim",
            "Bow_Follow_GRP_parentConstraint1",
            "Arrow_anim",
            "Arrow_LOC",
            "Arrow_Follow_GRP_parentConstraint1",
            "String_Reset_LOC",
            "String_anim",
            "L_arm_settings_anim",
            "R_arm_settings_anim",
            "IK_L_shoulder_jnt",
            "IK_L_elbow_jnt",
            "IK_L_wrist_jnt",
            "FK_L_shoulder_anim",
            "FK_L_elbow_anim",
            "FK_L_wrist_anim",
            "L_shoulder_skn_jnt",
            "L_elbow_skn_jnt",
            "L_wrist_skn_jnt",
            "Ik_L_hand_anim",
            "IK_L_elbow_anim",
        }
        self.aliases = {
            "Bow_Follow_GRP_parentConstraint1": ("L_bowW0", "R_bowW1"),
            "Arrow_Follow_GRP_parentConstraint1": (
                "L_arrowW0",
                "R_arrowW1",
            ),
        }
        self.attrs = {
            "Sword_CTRL.weaponSpace": 1,
            "Sword_Follow_GRP_parentConstraint1.nodeState": 0,
            "Shield_CTRL.shieldSpace": 1,
            "Shield_Follow_GRP_parentConstraint1.nodeState": 0,
            "ALL_Bow_anim.bowSpace": 1,
            "Bow_Follow_GRP_parentConstraint1.nodeState": 0,
            "Bow_Follow_GRP_parentConstraint1.L_bowW0": 0,
            "Bow_Follow_GRP_parentConstraint1.R_bowW1": 1,
            "Arrow_Follow_GRP_parentConstraint1.L_arrowW0": 1,
            "Arrow_Follow_GRP_parentConstraint1.R_arrowW1": 0,
            "L_arm_settings_anim.FKIK": 0,
            "R_arm_settings_anim.FKIK": 0,
        }
        self.matrices = {
            "Arrow_LOC": list(range(16)),
            "String_Reset_LOC": list(reversed(range(16))),
            "IK_L_shoulder_jnt": [1] * 16,
            "IK_L_elbow_jnt": [2] * 16,
            "IK_L_wrist_jnt": [3] * 16,
        }
        self.positions = {
            "L_shoulder_skn_jnt": (0.0, 0.0, 0.0),
            "L_elbow_skn_jnt": (1.0, 1.0, 0.0),
            "L_wrist_skn_jnt": (2.0, 0.0, 0.0),
            "IK_L_elbow_anim": (1.0, 3.0, 0.0),
        }

    def objExists(self, node):
        return node in self.nodes

    def attributeQuery(self, name, node, exists):
        return exists and "{}.{}".format(node, name) in self.attrs

    def getAttr(self, plug):
        return self.attrs[plug]

    def setAttr(self, plug, value):
        self.set_attr_calls.append((plug, value))
        self.attrs[plug] = value

    def parentConstraint(self, constraint, q=False, wal=False):
        if q and wal:
            return self.aliases[constraint]
        raise AssertionError("Unexpected parentConstraint mutation")

    def xform(
        self,
        node,
        q=False,
        ws=False,
        matrix=None,
        t=False,
        rotation=False,
    ):
        if q:
            if t:
                return self.positions[node]
            return self.matrices[node]
        if matrix is not None:
            self.xform_calls.append((node, matrix))
            self.matrices[node] = matrix
        elif t is not False:
            values = tuple(t)
            self.xform_calls.append((node, ("translation", values)))
            self.positions[node] = values

    def matchTransform(self, target, source, pos=False, rot=False):
        self.match_transform_calls.append((target, source, pos, rot))

    def setToolTo(self, _tool):
        pass

    def select(self, *_args, **_kwargs):
        pass

    def warning(self, message):
        self.messages.append(message)

    def inViewMessage(self, **kwargs):
        self.messages.append(kwargs["amg"])

    def refresh(self, **_kwargs):
        pass


class FakeEquipmentService:
    def __init__(self):
        self.calls = []
        self.scene_states = {
            "Sword": (Side.LEFT, True),
            "Shield": (Side.RIGHT, False),
            "Bow": (Side.LEFT, True),
        }

    def get_config(self, name):
        if name not in EQUIPMENT_CONFIGS:
            raise ValueError("Unsupported equipment: {}".format(name))
        return EQUIPMENT_CONFIGS[name]

    def get_scene_state(self, name):
        return self.scene_states[name]

    def get_current_side(self, name):
        return self.scene_states[name][0]

    def switch_side(self, name, side, follow_enabled=None):
        self.calls.append(("switch", name, side, follow_enabled))

    def is_follow_enabled(self, name):
        return self.scene_states[name][1]


class FakeBowService:
    def get_arrow_scene_state(self):
        return Side.RIGHT, True

    def get_string_follow_enabled(self, _bow_side):
        return False


class FakeUI:
    def __init__(self):
        self.states = []
        self.show_calls = 0

    def show(self):
        self.show_calls += 1

    def render(self, state, _config):
        self.states.append((state.current_equipment, state.equipment_side))


class EquipmentServiceStateTests(unittest.TestCase):
    def setUp(self):
        self.cmds = FakeSceneCmds()
        self.service = EquipmentService(self.cmds, EQUIPMENT_CONFIGS)

    def test_sword_side_from_space(self):
        self.assertEqual(self.service.get_current_side("Sword"), Side.LEFT)
        self.cmds.attrs["Sword_CTRL.weaponSpace"] = 0
        self.assertEqual(self.service.get_current_side("Sword"), Side.RIGHT)

    def test_shield_side_from_space(self):
        self.assertEqual(self.service.get_current_side("Shield"), Side.RIGHT)
        self.cmds.attrs["Shield_CTRL.shieldSpace"] = 0
        self.assertEqual(self.service.get_current_side("Shield"), Side.LEFT)

    def test_bow_space_zero_is_left(self):
        self.cmds.attrs["ALL_Bow_anim.bowSpace"] = 0
        self.assertEqual(self.service.get_current_side("Bow"), Side.LEFT)

    def test_bow_space_one_is_right(self):
        self.assertEqual(self.service.get_current_side("Bow"), Side.RIGHT)

    def test_zero_weights_keep_bow_side_and_mean_follow_off(self):
        constraint = "Bow_Follow_GRP_parentConstraint1"
        self.cmds.attrs[constraint + ".L_bowW0"] = 0
        self.cmds.attrs[constraint + ".R_bowW1"] = 0
        self.assertEqual(
            self.service.get_scene_state("Bow"), (Side.RIGHT, False)
        )

    def test_follow_off_side_switch_does_not_enable_constraint(self):
        constraint = "Bow_Follow_GRP_parentConstraint1"
        self.cmds.attrs[constraint + ".L_bowW0"] = 0
        self.cmds.attrs[constraint + ".R_bowW1"] = 0
        self.service.apply_offset = lambda *_args: None

        self.service.switch_side("Bow", Side.LEFT, follow_enabled=False)

        self.assertEqual(self.cmds.attrs["ALL_Bow_anim.bowSpace"], 0)
        self.assertEqual(self.cmds.attrs[constraint + ".L_bowW0"], 0)
        self.assertEqual(self.cmds.attrs[constraint + ".R_bowW1"], 0)

    def test_follow_on_side_switch_updates_constraint(self):
        constraint = "Bow_Follow_GRP_parentConstraint1"
        self.service.apply_offset = lambda *_args: None

        self.service.switch_side("Bow", Side.LEFT, follow_enabled=True)

        self.assertEqual(self.cmds.attrs["ALL_Bow_anim.bowSpace"], 0)
        self.assertEqual(self.cmds.attrs[constraint + ".L_bowW0"], 1)
        self.assertEqual(self.cmds.attrs[constraint + ".R_bowW1"], 0)

    def test_invalid_bow_space_has_clear_error(self):
        self.cmds.attrs["ALL_Bow_anim.bowSpace"] = 3
        with self.assertRaisesRegex(EquipmentAttributeError, "Expected 0 or 1"):
            self.service.get_current_side("Bow")

    def test_both_weights_active_is_invalid(self):
        constraint = "Bow_Follow_GRP_parentConstraint1"
        self.cmds.attrs[constraint + ".L_bowW0"] = 1
        self.cmds.attrs[constraint + ".R_bowW1"] = 1
        with self.assertRaises(ConstraintStateError):
            self.service.get_scene_state("Bow")


class BowServiceStateTests(unittest.TestCase):
    def setUp(self):
        self.cmds = FakeSceneCmds()
        self.service = BowService(
            self.cmds, ARROW_CONFIG, STRING_CONFIG
        )

    def test_arrow_follow_state_from_constraint(self):
        self.assertEqual(
            self.service.get_arrow_scene_state(), (Side.LEFT, True)
        )

    def test_arrow_reset_snaps_body_to_string_reference(self):
        expected = self.cmds.matrices["String_Reset_LOC"]
        self.service.reset_arrow_pose()
        self.assertEqual(self.cmds.xform_calls, [("Arrow_LOC", expected)])

    def test_string_follow_reads_arm_selected_by_bow_space_side(self):
        equipment_service = EquipmentService(
            self.cmds, EQUIPMENT_CONFIGS
        )
        bow_side = equipment_service.get_current_side("Bow")
        self.cmds.attrs["L_arm_settings_anim.FKIK"] = 1
        self.assertTrue(self.service.get_string_follow_enabled(bow_side))

    def test_ik_to_fk_matches_fk_controls_before_mode_switch(self):
        self.service.set_string_follow(False, Side.RIGHT)

        self.assertIn(
            (
                "FK_L_shoulder_anim",
                self.cmds.matrices["IK_L_shoulder_jnt"],
            ),
            self.cmds.xform_calls,
        )
        self.assertIn(
            ("FK_L_elbow_anim", self.cmds.matrices["IK_L_elbow_jnt"]),
            self.cmds.xform_calls,
        )
        self.assertIn(
            ("FK_L_wrist_anim", self.cmds.matrices["IK_L_wrist_jnt"]),
            self.cmds.xform_calls,
        )

    def test_fk_to_ik_matches_hand_and_pole_before_ik_mode(self):
        self.service.set_string_follow(True, Side.RIGHT)

        self.assertEqual(self.cmds.attrs["L_arm_settings_anim.FKIK"], 1)
        self.assertEqual(
            self.cmds.match_transform_calls,
            [("Ik_L_hand_anim", "L_wrist_skn_jnt", True, True)],
        )
        self.assertIn(
            "IK_L_elbow_anim",
            [call[0] for call in self.cmds.xform_calls],
        )

    def test_pole_position_stays_on_arm_plane(self):
        result = self.service._calculate_pole_position(
            shoulder=(0.0, 0.0, 0.0),
            elbow=(1.0, 1.0, 0.0),
            wrist=(2.0, 0.0, 0.0),
        )
        self.assertAlmostEqual(result[0], 1.0)
        self.assertAlmostEqual(result[1], 1.0 + 2.0 * math.sqrt(2.0))
        self.assertAlmostEqual(result[2], 0.0)


class ControllerStateTests(unittest.TestCase):
    def setUp(self):
        self.cmds = FakeSceneCmds()
        self.service = FakeEquipmentService()
        self.state = EquipmentState()
        self.controller = EquipmentController(
            self.cmds, self.service, FakeBowService(), self.state
        )
        self.ui = FakeUI()
        self.controller.attach_ui(self.ui)

    def test_tab_switch_reads_that_equipments_scene_side(self):
        self.controller.select_equipment("Shield")
        self.assertEqual(self.state.current_equipment, "Shield")
        self.assertEqual(self.state.equipment_side, Side.RIGHT)
        self.assertFalse(self.state.equipment_follow_enabled)

        self.controller.select_equipment("Bow")
        self.assertEqual(self.state.equipment_side, Side.LEFT)
        self.assertTrue(self.state.equipment_follow_enabled)

    def test_hand_switch_updates_state_after_service(self):
        self.controller.switch_equipment_hand(Side.LEFT)
        self.assertEqual(self.state.equipment_side, Side.LEFT)
        self.assertEqual(
            self.service.calls[-1],
            ("switch", "Sword", Side.LEFT, None),
        )
        self.assertIn("SWORD LEFT", self.cmds.messages[-1])


class AppStartupTests(unittest.TestCase):
    def test_show_reads_scene_without_set_attr(self):
        cmds = FakeSceneCmds()
        app = EquipmentManagerApp(cmds)
        ui = FakeUI()
        app.ui = ui
        app.controller.attach_ui(ui)

        app.show()

        self.assertEqual(cmds.set_attr_calls, [])
        self.assertEqual(ui.show_calls, 1)
        self.assertEqual(app.state.equipment_side, Side.LEFT)
        self.assertEqual(app.state.arrow_side, Side.LEFT)

    def test_both_arrow_weights_emit_warning_and_remain_unknown(self):
        cmds = FakeSceneCmds()
        constraint = "Arrow_Follow_GRP_parentConstraint1"
        cmds.attrs[constraint + ".L_arrowW0"] = 1
        cmds.attrs[constraint + ".R_arrowW1"] = 1
        app = EquipmentManagerApp(cmds)
        ui = FakeUI()
        app.ui = ui
        app.controller.attach_ui(ui)

        app.show()

        self.assertIsNone(app.state.arrow_side)
        self.assertIsNone(app.state.arrow_follow_enabled)
        self.assertTrue(
            any("Both left and right weights" in item for item in cmds.messages)
        )


class UtilityAndLabelTests(unittest.TestCase):
    def test_invalid_side_is_rejected(self):
        with self.assertRaises(ValueError):
            side_weights("L")

    def test_constraint_helpers(self):
        self.assertEqual(side_weights(Side.LEFT), (1, 0))
        self.assertEqual(
            resolve_side_aliases(("R_socketW1", "L_socketW0")),
            ("L_socketW0", "R_socketW1"),
        )

    def test_ui_labels(self):
        self.assertEqual(
            EquipmentManagerUI.hand_label(Side.LEFT, True), "✓ L_HAND"
        )
        self.assertEqual(
            EquipmentManagerUI.follow_label(True, True), "✓ FOLLOW ON"
        )


if __name__ == "__main__":
    unittest.main()
