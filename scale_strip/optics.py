"""The optics half: film-plane distance for an extension, and its inverse.

For a lens that focuses by moving as a rigid unit, which is what the helicoid
does, the thin-lens relation gives the film-plane-to-subject distance in closed
form. All quantities here are in millimeters; ``hf`` is the per-lens internodal
offset, zero by default. See design_docs/generator_math.md for the derivation.
"""

import math


def distance_mm(f: float, e: float, hf: float = 0.0) -> float:
    """Subject distance from the film plane for extension ``e`` past infinity."""
    if e <= 0.0:
        return math.inf
    return (f + e) ** 2 / e + hf


def extension_mm(f: float, distance: float, hf: float = 0.0) -> float:
    """Extension past infinity that focuses at ``distance`` from the film plane.

    Inverts ``distance_mm``. The equation is the quadratic
    ``e**2 - (D' - 2f) e + f**2 = 0`` with ``D' = distance - hf``. The naive root
    subtracts two nearly equal large numbers near infinity and loses precision,
    so this uses the algebraically equal form built from the roots' product
    ``f**2``, which stays accurate across the whole range.
    """
    if math.isinf(distance):
        return 0.0
    dp = distance - hf
    b = dp - 2.0 * f
    disc = b * b - 4.0 * f * f  # equals dp*(dp - 4f); non-negative for e <= f
    if disc < 0.0:
        raise ValueError(
            f"distance {distance:.3f}mm is closer than 1:1 for f={f}mm; "
            "no extension on this helicoid focuses there"
        )
    return 2.0 * f * f / (b + math.sqrt(disc))


def mfd_mm(f: float, ext_max: float, hf: float = 0.0) -> float:
    """Minimum focus distance from the film plane, at full extension."""
    return distance_mm(f, ext_max, hf)
