"""Choosing which distances to mark, and where they land.

Two steps: generate candidate distances on round numbers, then select a subset
that reads cleanly. This is the deliberately rough first cut. The spacing is
meant to be tuned later, so the logic stays behind ``select_marks`` and leans on
the constants in ``config``.
"""

from dataclasses import dataclass

from . import config, geometry, optics
from .units import Unit, format_distance, from_mm, to_mm

# Mantissa roundness, higher preferred. Used only to break ties when the
# selector must choose between candidates competing for the same gap.
_MANTISSA_PRIORITY = {
    1.0: 6, 5.0: 5, 2.0: 4, 3.0: 3, 1.5: 2, 2.5: 2, 7.0: 2, 4.0: 1, 6.0: 1, 8.0: 1, 9.0: 1,
}
_EXPONENTS = range(-1, 4)  # 0.1x through 1000x


@dataclass(frozen=True)
class MarkSpec:
    e_mm: float
    x_mm: float
    value: float   # distance in display units
    label: str
    priority: int


def _valid_for_unit(value: float, unit: Unit) -> bool:
    """Feet take whole or half values; meters take one decimal place."""
    step = 2.0 if unit is Unit.FEET else 10.0
    scaled = value * step
    return abs(scaled - round(scaled)) < 1e-9


def candidate_values(unit: Unit, d_min: float, d_max: float):
    """Round display-unit distances in ``(d_min, d_max)``, with priorities."""
    out = []
    seen = set()
    for k in _EXPONENTS:
        scale = 10.0 ** k
        for mant, prio in _MANTISSA_PRIORITY.items():
            value = round(mant * scale, 6)
            if value <= d_min or value >= d_max:
                continue
            if not _valid_for_unit(value, unit):
                continue
            if value in seen:
                continue
            seen.add(value)
            out.append((value, prio))
    out.sort()
    return out


def _slot_bands(slots):
    """Forbidden x ranges around slots, as (lo, hi) pairs."""
    half = config.SLOT_SPAN_MM / 2.0 + config.SLOT_AVOID_MARGIN_MM
    return [(s.x_mm - half, s.x_mm + half) for s in slots]


def _in_band(x: float, bands) -> bool:
    return any(lo <= x <= hi for lo, hi in bands)


def select_marks(f: float, unit: Unit, hf: float, slots) -> list[MarkSpec]:
    """Intermediate marks for one lens, between infinity and minimum focus.

    Infinity and the minimum-focus mark are added by the model; this returns the
    marks in between. The walk prefers round numbers, keeps marks at least the
    minimum gap apart and at most the maximum apart, skips slot bands, and allows
    up to double the maximum gap where a slot sits in the way.
    """
    x_inf = geometry.x_infinity()
    x_mfd = geometry.x_mfd()
    bands = _slot_bands(slots)

    d_mfd = optics.mfd_mm(f, config.EXT_MAX_MM, hf)
    d_min = from_mm(d_mfd, unit)
    d_max = from_mm(optics.distance_mm(f, _near_infinity_extension(), hf), unit)

    cands = []
    for value, prio in candidate_values(unit, d_min, d_max):
        e = optics.extension_mm(f, to_mm(value, unit), hf)
        x = geometry.x_from_extension(e)
        if x <= x_inf or x >= x_mfd:
            continue
        if _in_band(x, bands):
            continue
        cands.append(MarkSpec(e, x, value, format_distance(value, unit), prio))
    cands.sort(key=lambda c: c.x_mm)

    selected = []
    last = x_inf
    while True:
        lo = last + config.MIN_MARK_GAP_MM
        hi = last + config.MAX_MARK_GAP_MM
        if any(last < bhi and lo < bhi and blo <= hi for blo, bhi in bands):
            hi = last + 2.0 * config.MAX_MARK_GAP_MM  # let a slot widen the gap
        window = [c for c in cands if lo <= c.x_mm <= hi]
        if window:
            pick = max(window, key=lambda c: (c.priority, c.x_mm))
        else:
            beyond = [c for c in cands if c.x_mm >= lo]
            if not beyond:
                break
            pick = beyond[0]
        if pick.x_mm >= x_mfd - config.MIN_MARK_GAP_MM:
            break
        selected.append(pick)
        last = pick.x_mm
        cands = [c for c in cands if c.x_mm > last]

    return selected


def _near_infinity_extension() -> float:
    """Extension at the closest mark-bearing position to infinity.

    A hair past infinity, so the candidate range has a finite far limit instead
    of running to true infinity.
    """
    return geometry.extension_from_x(geometry.x_infinity() + config.MIN_MARK_GAP_MM)
