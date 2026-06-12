"""PDF output: the strip at true size, plus calibration lines.

The page uses millimeter coordinates with no scaling, so a 10 mm line prints as
10 mm when the PDF is printed at actual size. That, and the 1 inch line beside
it, let the user confirm scale on paper. The strip itself draws at 1:1, which
makes its text small but real. Layout sizes are constants here since they
interact with the tight strip width and will be tuned.
"""

from fpdf import FPDF

from .model import MarkKind, StripModel

# Page placement and element sizes, all millimeters except font size in points.
_MARGIN_TOP_MM = 22.0
_STRIP_GAP_MM = 8.0      # blank band between stacked strips
_ROW_MARGIN_MM = 0.3     # blank band at the strip's top and bottom edges
_DOT_R_MM = 0.32
_INF_R_MM = 0.42
_LABEL_GAP_MM = 0.7      # dot to its number
_MAX_MARK_MM = 3.2       # cap on mark-number height (one row would exceed it)
_LEGEND_FONT_PT = 5.0
_PT_PER_MM = 2.83465

_PAGE_W = {"letter": 279.4, "a4": 297.0}


def render_pdf(models, page: str = "letter") -> bytes:
    """Render one or more strips onto a single page.

    ``models`` is a ``StripModel`` or a list of them. Each becomes a strip,
    stacked down the page with one calibration block below. The website puts a
    focus strip and the debug strip together this way.
    """
    if isinstance(models, StripModel):
        models = [models]
    pdf = FPDF(orientation="L", unit="mm", format=page)
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_line_width(0.15)

    margin_x = (_PAGE_W.get(page, _PAGE_W["letter"]) - models[0].outline.length_mm) / 2.0
    _draw_title(pdf, models, margin_x)

    top = _MARGIN_TOP_MM
    for model in models:
        _draw_strip(pdf, model, margin_x, top)
        top += model.outline.width_mm + _STRIP_GAP_MM

    # The calibration block sits off the strips, black on the white page.
    _set_color(pdf, 0)
    _draw_calibration(pdf, margin_x, top + 4.0)
    return bytes(pdf.output())


def _draw_strip(pdf, model, margin_x, top):
    # The strip is a black field with everything on it in white, like the metal
    # original. Fill it black, then draw the marks, text, and slots in white.
    def px(x):
        return margin_x + x

    def py(y):
        return top + y

    _draw_outline(pdf, model, px, py)
    _set_color(pdf, 255)
    _draw_slots(pdf, model, px, py)
    _draw_infinity_line(pdf, model, px, py)
    _draw_rows(pdf, model, px, py)
    _draw_legends(pdf, model, px, py)
    _set_color(pdf, 0)


def _set_color(pdf, level):
    pdf.set_draw_color(level)
    pdf.set_fill_color(level)
    pdf.set_text_color(level)


def _draw_title(pdf, models, x):
    pdf.set_font("Helvetica", size=9)
    focals = [r.focal_length for m in models for r in m.rows if r.focal_length is not None]
    unit = next((m.unit for m in models if m.unit is not None), None)
    has_debug = any(m.debug for m in models)
    if focals:
        lenses = ", ".join(str(f) for f in focals)
        what = f"Bronica S2 focusing scale  {unit.value.capitalize()}  {lenses} mm"
        if has_debug:
            what += "  + extension strip"
    else:
        what = "Bronica S2 helicoid extension strip (mm)"
    pdf.text(x, 12.0, what)
    pdf.set_font("Helvetica", size=7)
    pdf.text(x, 16.5, "Print at 100% (actual size). Check the lines below with a ruler.")


def _draw_outline(pdf, model, px, py):
    o = model.outline
    pdf.set_fill_color(0)
    # Semicircular ends: a corner radius of half the width makes the ends round.
    pdf.rect(px(0), py(0), o.length_mm, o.width_mm, style="F",
             round_corners=True, corner_radius=o.width_mm / 2.0)


def _draw_slots(pdf, model, px, py):
    cy = model.outline.width_mm / 2.0
    for s in model.slots:
        pdf.rect(px(s.x_mm - s.span_mm / 2.0), py(cy - s.width_mm / 2.0),
                 s.span_mm, s.width_mm, style="D",
                 round_corners=True, corner_radius=s.width_mm / 2.0)


def _mark_font_pt(model):
    # Numbers grow as the rows do: a one-row strip (the debug strip) gets the
    # biggest, three rows the smallest, capped so they never swamp the strip.
    n = max(1, len(model.rows))
    row_h = (model.outline.width_mm - 2 * _ROW_MARGIN_MM) / n
    return min(_MAX_MARK_MM, 0.74 * row_h) * _PT_PER_MM


def _draw_rows(pdf, model, px, py):
    font_pt = _mark_font_pt(model)
    pdf.set_font("Helvetica", size=font_pt)
    for row in model.rows:
        yc = row.y_center_mm
        for mark in row.marks:
            if mark.kind is MarkKind.INFINITY:
                _draw_infinity(pdf, px(mark.x_mm), py(yc))
                continue
            _dot(pdf, px(mark.x_mm), py(yc))
            if mark.label:
                pdf.text(px(mark.x_mm) + _LABEL_GAP_MM, py(yc) + font_pt * 0.18,
                         mark.label)


def _dot(pdf, cx, cy):
    r = _DOT_R_MM
    pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r, style="F")


def _draw_infinity_line(pdf, model, px, py):
    x = px(model.infinity_x_mm)
    pdf.set_line_width(0.18)
    pdf.line(x, py(0.2), x, py(model.outline.width_mm - 0.2))


def _draw_infinity(pdf, cx, cy):
    # Symbol to the right of the infinity line.
    r = _INF_R_MM
    x0 = cx + 0.45
    pdf.ellipse(x0, cy - r, 2 * r, 2 * r, style="D")
    pdf.ellipse(x0 + 2 * r - 0.15, cy - r, 2 * r, 2 * r, style="D")


def _draw_legends(pdf, model, px, py):
    pdf.set_font("Helvetica", size=_LEGEND_FONT_PT)
    for row in model.rows:
        y = py(row.y_center_mm) + _LEGEND_FONT_PT * 0.18
        pdf.text(px(model.legend_x_left_mm) - 1.0, y, row.legend)
        pdf.text(px(model.legend_x_right_mm), y, row.legend)
    _draw_unit_labels(pdf, model, px, py)


def _draw_unit_labels(pdf, model, px, py):
    # In the roomy left legend margin, just before the infinity line.
    pdf.set_font("Helvetica", size=_LEGEND_FONT_PT)
    y = py(model.outline.width_mm / 2.0 + _LEGEND_FONT_PT * 0.18)
    pdf.text(px(model.infinity_x_mm - 5.5), y, model.unit_label)


def _draw_calibration(pdf, x, y):
    pdf.set_font("Helvetica", size=8)
    pdf.text(x, y - 2.0, "Scale check:")
    _ref_line(pdf, x, y + 3.0, 10.0, "1 cm")
    _ref_line(pdf, x, y + 9.0, 25.4, "1 in")


def _ref_line(pdf, x, y, length, label):
    pdf.set_line_width(0.2)
    pdf.line(x, y, x + length, y)
    pdf.line(x, y - 1.0, x, y + 1.0)
    pdf.line(x + length, y - 1.0, x + length, y + 1.0)
    pdf.set_font("Helvetica", size=7)
    pdf.text(x + length + 2.0, y + 0.8, label)
