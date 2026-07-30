"""All UI and rig-dependent constants used by Equipment Manager."""

from .models import ArrowConfig, EquipmentConfig, StringConfig


WINDOW_NAME = "EquipmentManager"
CHECK_MARK = "\u2713"
TRANSFORM_CHANNELS = ("tx", "ty", "tz", "rx", "ry", "rz")

SWORD_ACTIVE_COLOR = (0.46, 0.34, 0.34)
SWORD_BASE_COLOR = (0.38, 0.35, 0.35)
SHIELD_ACTIVE_COLOR = (0.66, 0.60, 0.36)
SHIELD_BASE_COLOR = (0.46, 0.43, 0.33)
BOW_ACTIVE_COLOR = (0.28, 0.48, 0.78)
BOW_BASE_COLOR = (0.24, 0.30, 0.38)
ARROW_BASE_COLOR = (0.38, 0.38, 0.38)

EQUIPMENT_CONFIGS = {
    "Sword": EquipmentConfig(
        name="Sword",
        control="Sword_CTRL",
        constraint="Sword_Follow_GRP_parentConstraint1",
        space_attribute="weaponSpace",
        title="Weapon Grip",
        active_color=SWORD_ACTIVE_COLOR,
        base_color=SWORD_BASE_COLOR,
    ),
    "Shield": EquipmentConfig(
        name="Shield",
        control="Shield_CTRL",
        constraint="Shield_Follow_GRP_parentConstraint1",
        space_attribute="shieldSpace",
        title="Shield Grip",
        active_color=SHIELD_ACTIVE_COLOR,
        base_color=SHIELD_BASE_COLOR,
    ),
    "Bow": EquipmentConfig(
        name="Bow",
        control="ALL_Bow_anim",
        constraint="Bow_Follow_GRP_parentConstraint1",
        space_attribute="bowSpace",
        title="Bow Grip",
        active_color=BOW_ACTIVE_COLOR,
        base_color=BOW_BASE_COLOR,
    ),
}

ARROW_CONFIG = ArrowConfig(
    control="Arrow_anim",
    constraint="Arrow_Follow_GRP_parentConstraint1",
    body="Arrow_LOC",
    reset_reference="String_Reset_LOC",
)

STRING_CONFIG = StringConfig(
    control="String_anim",
    draw_attributes=("Normal_Draw", "Light_Draw", "FullDraw"),
    translate_attributes=("translateX", "translateY", "translateZ"),
    fk_match_pairs=(
        ("IK_{side}_shoulder_jnt", "FK_{side}_shoulder_anim"),
        ("IK_{side}_elbow_jnt", "FK_{side}_elbow_anim"),
        ("IK_{side}_wrist_jnt", "FK_{side}_wrist_anim"),
    ),
    ik_shoulder_joint="{side}_shoulder_skn_jnt",
    ik_elbow_joint="{side}_elbow_skn_jnt",
    ik_wrist_joint="{side}_wrist_skn_jnt",
    ik_hand_control="Ik_{side}_hand_anim",
    ik_pole_control="IK_{side}_elbow_anim",
)
