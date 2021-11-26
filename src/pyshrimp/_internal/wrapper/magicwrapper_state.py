from dataclasses import dataclass


@dataclass
class _MagicState:
    active: bool


_MAGIC_STATE = _MagicState(
    active=False
)


def _is_magic_active():
    return _MAGIC_STATE.active
