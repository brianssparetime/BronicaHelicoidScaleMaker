"""Display units and distance formatting.

Geometry is computed in millimeters everywhere. Units enter only when choosing
which round distances to mark and when writing their labels. The strip shows a
bare number with no unit suffix, as the stock strip does.
"""

from enum import Enum

MM_PER_FOOT = 304.8
MM_PER_METER = 1000.0


class Unit(Enum):
    FEET = "feet"
    METERS = "meters"

    @property
    def mm_per_unit(self) -> float:
        return MM_PER_FOOT if self is Unit.FEET else MM_PER_METER

    @property
    def symbol(self) -> str:
        return "ft" if self is Unit.FEET else "m"


def to_mm(value: float, unit: Unit) -> float:
    return value * unit.mm_per_unit


def from_mm(mm: float, unit: Unit) -> float:
    return mm / unit.mm_per_unit


def format_distance(value: float, unit: Unit) -> str:
    """Format a distance value for the strip, without a unit suffix.

    Feet print as a whole number or with a single ``.5``. Meters print to one
    decimal, dropping a trailing ``.0``. Both match the vision's number rules.
    """
    if unit is Unit.FEET:
        if abs(value - round(value)) < 1e-6:
            return str(int(round(value)))
        return f"{value:.1f}"  # halves only reach here, e.g. 1.5
    # Meters: one decimal, trailing .0 dropped.
    text = f"{value:.1f}"
    if text.endswith(".0"):
        return text[:-2]
    return text


def format_mfd(value: float) -> str:
    """Format a minimum-focus distance, which is exempt from the round-number
    rules. Shows the true value: two decimals under ten, one decimal above,
    with trailing zeros dropped.
    """
    decimals = 1 if value >= 10 else 2
    text = f"{value:.{decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
