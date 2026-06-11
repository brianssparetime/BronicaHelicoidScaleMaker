"""The geometry half: extension to position along the strip, and back.

The helicoid is a constant-pitch screw, so extension grows linearly with
rotation, and the strip is that rotation unrolled flat. Position is therefore
linear in extension. This half is shared by every lens; all the nonlinearity
lives in the optics. Positions are millimeters in the strip frame, x measured
from the left tab tip, with infinity at ``INF_OFFSET_MM``.
"""

from . import config


def x_from_extension(e: float) -> float:
    """Strip position for an extension past infinity."""
    return config.INF_OFFSET_MM + config.L_SCALE_MM * (e / config.EXT_MAX_MM)


def extension_from_x(x: float) -> float:
    """Extension past infinity for a strip position. Inverse of the above."""
    return (x - config.INF_OFFSET_MM) * config.EXT_MAX_MM / config.L_SCALE_MM


def x_infinity() -> float:
    return config.INF_OFFSET_MM


def x_mfd() -> float:
    return config.INF_OFFSET_MM + config.L_SCALE_MM
