from scale_strip.model import build_model
from scale_strip.render_dxf import render_dxf
from scale_strip.render_pdf import render_pdf
from scale_strip.units import Unit


def test_pdf_is_a_pdf():
    data = render_pdf(build_model(Unit.METERS, [50, 75, 150]))
    assert data[:4] == b"%PDF"
    assert b"%%EOF" in data
    assert len(data) > 1000


def test_pdf_page_is_letter_landscape():
    data = render_pdf(build_model(Unit.METERS, [75]), page="letter")
    # Letter landscape is 792 x 612 points.
    assert b"/MediaBox" in data
    assert b"792" in data and b"612" in data


def test_pdf_a4_renders():
    data = render_pdf(build_model(Unit.METERS, [75]), page="a4")
    assert data[:4] == b"%PDF"


def test_pdf_debug_renders():
    data = render_pdf(build_model(None, [], debug=True))
    assert data[:4] == b"%PDF"


def test_dxf_structure_and_layers():
    text = render_dxf(build_model(Unit.METERS, [50, 75, 150])).decode("ascii")
    assert text.startswith("0\nSECTION")
    assert text.rstrip().endswith("EOF")
    for token in ("CUT", "ENGRAVE", "POLYLINE", "CIRCLE", "TEXT", "AC1009"):
        assert token in text, token
    assert text.count("0\nSECTION") == text.count("0\nENDSEC")


def test_dxf_has_outline_and_three_slots():
    text = render_dxf(build_model(Unit.METERS, [75])).decode("ascii")
    # Outline plus three slots are four closed polylines.
    assert text.count("0\nPOLYLINE") == 4
