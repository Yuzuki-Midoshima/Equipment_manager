"""Domain errors shown to animators without exposing raw tracebacks."""


class EquipmentManagerError(RuntimeError):
    """Base class for expected Equipment Manager failures."""


class EquipmentNodeError(EquipmentManagerError):
    """Raised when a configured Maya node is missing."""


class EquipmentAttributeError(EquipmentManagerError):
    """Raised when a required Maya attribute is missing."""


class ConstraintAliasError(EquipmentManagerError):
    """Raised when left/right constraint weights cannot be resolved."""


class ConstraintStateError(EquipmentManagerError):
    """Raised when constraint weights describe an invalid simultaneous state."""
