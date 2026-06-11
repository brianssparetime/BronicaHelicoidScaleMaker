"""DXF output: a hand-rolled R12 ASCII drawing, no third-party library.

Two layers. CUT carries the strip outline and the slots, as closed polylines
with arc bulges on the rounded parts. ENGRAVE carries the dots as circles and
the labels as TEXT. R12 ASCII is the most widely accepted flavor in laser
software, and the entity set here is small enough to emit directly. Units are
millimeters. The model frame has y running down from the strip top; DXF is y-up,
so y flips here.
"""

from .model import MarkKind, StripModel

_CUT = "CUT"
_ENGRAVE = "ENGRAVE"
_DOT_R = 0.32
_INF_R = 0.42
_TEXT_H = 1.4
_LABEL_GAP = 0.7


class _Dxf:
    """Accumulates R12 group-code pairs."""

    def __init__(self):
        self._lines = []

    def pair(self, code, value):
        self._lines.append(str(code))
        if isinstance(value, float):
            self._lines.append(f"{value:.4f}")
        else:
            self._lines.append(str(value))

    def text(self):
        return "\n".join(self._lines) + "\n"


def render_dxf(model: StripModel) -> bytes:
    d = _Dxf()
    _header(d)
    _tables(d)
    _entities(d, model)
    d.pair(0, "EOF")
    return d.text().encode("ascii")


def _header(d):
    d.pair(0, "SECTION"); d.pair(2, "HEADER")
    d.pair(9, "$ACADVER"); d.pair(1, "AC1009")
    d.pair(9, "$INSUNITS"); d.pair(70, 4)  # millimeters
    d.pair(0, "ENDSEC")


def _tables(d):
    d.pair(0, "SECTION"); d.pair(2, "TABLES")
    d.pair(0, "TABLE"); d.pair(2, "LAYER"); d.pair(70, 2)
    _layer(d, _CUT, 1)       # red, conventional for cut
    _layer(d, _ENGRAVE, 7)   # white/black, for engrave
    d.pair(0, "ENDTAB")
    d.pair(0, "ENDSEC")


def _layer(d, name, color):
    d.pair(0, "LAYER"); d.pair(2, name); d.pair(70, 0)
    d.pair(62, color); d.pair(6, "CONTINUOUS")


def _entities(d, model):
    d.pair(0, "SECTION"); d.pair(2, "ENTITIES")
    w = model.outline.width_mm

    def fy(y):  # model y (down from top) to DXF y (up)
        return w - y

    # Strip outline as an obround: straight edges, semicircular ends.
    _obround(d, _CUT, model.outline.length_mm / 2.0, w / 2.0,
             model.outline.length_mm, w)
    for s in model.slots:
        _obround(d, _CUT, s.x_mm, w / 2.0, s.span_mm, s.width_mm)

    _line(d, _ENGRAVE, model.infinity_x_mm, 0.2, model.infinity_x_mm, w - 0.2)

    for row in model.rows:
        yc = fy(row.y_center_mm)
        for mark in row.marks:
            if mark.kind is MarkKind.INFINITY:
                _infinity(d, mark.x_mm, yc)
                continue
            _circle(d, _ENGRAVE, mark.x_mm, yc, _DOT_R)
            if mark.label:
                _text(d, _ENGRAVE, mark.x_mm + _LABEL_GAP, yc - _TEXT_H / 2.0,
                      _TEXT_H, mark.label)
        _text(d, _ENGRAVE, model.legend_x_left_mm - 1.0, yc - _TEXT_H / 2.0,
              _TEXT_H, row.legend)
        _text(d, _ENGRAVE, model.legend_x_right_mm, yc - _TEXT_H / 2.0,
              _TEXT_H, row.legend)

    # Unit label in the roomy left legend margin, before the infinity line.
    _text(d, _ENGRAVE, model.infinity_x_mm - 5.5, w / 2.0 - _TEXT_H / 2.0,
          _TEXT_H, model.unit_label)
    d.pair(0, "ENDSEC")


def _circle(d, layer, x, y, r):
    d.pair(0, "CIRCLE"); d.pair(8, layer)
    d.pair(10, float(x)); d.pair(20, float(y)); d.pair(30, 0.0)
    d.pair(40, float(r))


def _infinity(d, x, y):
    # Symbol to the right of the infinity line.
    c1 = x + 0.45 + _INF_R
    _circle(d, _ENGRAVE, c1, y, _INF_R)
    _circle(d, _ENGRAVE, c1 + 2 * _INF_R - 0.15, y, _INF_R)


def _line(d, layer, x1, y1, x2, y2):
    d.pair(0, "LINE"); d.pair(8, layer)
    d.pair(10, float(x1)); d.pair(20, float(y1)); d.pair(30, 0.0)
    d.pair(11, float(x2)); d.pair(21, float(y2)); d.pair(31, 0.0)


def _text(d, layer, x, y, height, s, rotation=0.0):
    d.pair(0, "TEXT"); d.pair(8, layer)
    d.pair(10, float(x)); d.pair(20, float(y)); d.pair(30, 0.0)
    d.pair(40, float(height))
    d.pair(1, s)
    if rotation:
        d.pair(50, float(rotation))


def _polyline(d, layer, verts, closed=True):
    """verts: list of (x, y, bulge)."""
    d.pair(0, "POLYLINE"); d.pair(8, layer)
    d.pair(66, 1)                 # vertices follow
    d.pair(70, 1 if closed else 0)
    for x, y, bulge in verts:
        d.pair(0, "VERTEX"); d.pair(8, layer)
        d.pair(10, float(x)); d.pair(20, float(y)); d.pair(30, 0.0)
        if bulge:
            d.pair(42, float(bulge))
    d.pair(0, "SEQEND")


def _obround(d, layer, cx, cy, span, width):
    r = width / 2.0
    half = span / 2.0 - r
    verts = [
        (cx - half, cy - r, 0.0),
        (cx + half, cy - r, 1.0),  # right semicircle cap
        (cx + half, cy + r, 0.0),
        (cx - half, cy + r, 1.0),  # left semicircle cap
    ]
    _polyline(d, layer, verts, closed=True)
