"""The abstract strip the renderers draw.

``build_model`` turns a unit and focal lengths into a ``StripModel`` in
millimeters in the strip frame: x along the length from the left tab tip, y
across the width from the top edge downward. Renderers map that frame onto a
page or a drawing. Nothing here knows about PDF or DXF.
"""

from dataclasses import dataclass, field
from enum import Enum

from . import config, geometry, optics
from .marks import select_marks
from .units import Unit, format_mfd, from_mm


class MarkKind(Enum):
    INFINITY = "infinity"
    MFD = "mfd"
    INTERMEDIATE = "intermediate"


@dataclass(frozen=True)
class Mark:
    x_mm: float
    label: str
    kind: MarkKind


@dataclass(frozen=True)
class Row:
    focal_length: int | None  # None for the debug strip
    y_center_mm: float
    legend: str               # focal length, or "mm" for the debug strip
    marks: list[Mark]


@dataclass(frozen=True)
class Slot:
    x_mm: float
    span_mm: float
    width_mm: float


@dataclass(frozen=True)
class Outline:
    length_mm: float
    width_mm: float
    corner_r_mm: float


@dataclass(frozen=True)
class StripModel:
    unit: Unit | None         # None for the debug strip
    rows: list[Row]
    outline: Outline
    slots: list[Slot]
    legend_x_left_mm: float
    legend_x_right_mm: float
    unit_label: str
    infinity_x_mm: float
    debug: bool = False


_ROW_MARGIN_MM = 0.3  # blank band at the top and bottom edges


def _slots() -> list[Slot]:
    return [
        Slot(config.LEFT_SLOT_X_MM, config.SLOT_SPAN_MM, config.SLOT_WIDTH_MM),
        Slot(config.CENTRAL_SLOT_X_MM, config.SLOT_SPAN_MM, config.SLOT_WIDTH_MM),
        Slot(config.RIGHT_SLOT_X_MM, config.SLOT_SPAN_MM, config.SLOT_WIDTH_MM),
    ]


def _row_centers(n: int) -> list[float]:
    usable = config.STRIP_W_MM - 2.0 * _ROW_MARGIN_MM
    row_h = usable / n
    return [_ROW_MARGIN_MM + (i + 0.5) * row_h for i in range(n)]


def build_model(unit, focal_lengths, *, debug=False, hf=None) -> StripModel:
    """Build one strip: focus scales for the focal lengths, or the debug strip.

    Each focal length gets a row, shortest at the top. ``debug=True`` returns the
    extension reference strip instead: one row in millimeters, reading 0 at
    infinity to the full travel. It stands alone. The website and command line
    render a focus strip and a debug strip into one PDF when both are wanted.
    """
    outline = Outline(config.STRIP_LEN_MM, config.STRIP_W_MM, config.CORNER_R_MM)
    slots = _slots()
    # Focal-length legend sits between the left slot and infinity, and after MFD.
    legend_left = config.LEFT_SLOT_X_MM + config.SLOT_SPAN_MM / 2.0 + 0.6
    legend_right = geometry.x_mfd() + 6.0

    if debug:
        row = _debug_row(_row_centers(1)[0])
        return StripModel(None, [row], outline, slots, legend_left, legend_right,
                          "mm", geometry.x_infinity(), debug=True)

    unit_obj = unit if isinstance(unit, Unit) else Unit(unit)
    hf = hf or config.HF_MM
    focals = sorted(set(int(f) for f in focal_lengths))
    if not focals:
        raise ValueError("no focal lengths given")
    centers = _row_centers(len(focals))

    rows = [Row(f, y, str(f), _lens_marks(f, unit_obj, hf.get(f, 0.0)))
            for f, y in zip(focals, centers)]
    return StripModel(unit_obj, rows, outline, slots, legend_left, legend_right,
                      unit_obj.symbol, geometry.x_infinity())


def _lens_marks(f: int, unit: Unit, hf: float) -> list[Mark]:
    # The minimum-focus mark shows the true MFD, exempt from the round-number
    # rules, so it is accurate at the hard stop.
    d_mfd = optics.mfd_mm(f, config.EXT_MAX_MM, hf)
    mfd_label = format_mfd(from_mm(d_mfd, unit))

    marks = [Mark(geometry.x_infinity(), "", MarkKind.INFINITY)]
    for m in select_marks(f, unit, hf, _slots()):
        # Defensive: a round intermediate rarely matches the true MFD label, but
        # if it does, the MFD mark is authoritative.
        if m.label == mfd_label:
            continue
        marks.append(Mark(m.x_mm, m.label, MarkKind.INTERMEDIATE))
    marks.append(Mark(geometry.x_mfd(), mfd_label, MarkKind.MFD))
    return marks


def _debug_row(y: float) -> Row:
    marks = []
    for e in range(0, int(config.EXT_MAX_MM) + 1):
        marks.append(Mark(geometry.x_from_extension(e), str(e), MarkKind.INTERMEDIATE))
    return Row(None, y, "mm", marks)
