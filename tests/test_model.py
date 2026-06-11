import pytest

from scale_strip import config, geometry
from scale_strip.model import MarkKind, build_model
from scale_strip.units import Unit


def test_rows_sorted_shortest_on_top():
    m = build_model(Unit.METERS, [150, 50, 75])
    focals = [r.focal_length for r in m.rows]
    assert focals == [50, 75, 150]
    ys = [r.y_center_mm for r in m.rows]
    assert ys == sorted(ys)  # shortest at the smallest y, the top


def test_infinity_and_mfd_columns_align():
    m = build_model(Unit.FEET, [50, 100, 200])
    for r in m.rows:
        assert r.marks[0].kind is MarkKind.INFINITY
        assert r.marks[-1].kind is MarkKind.MFD
        assert r.marks[0].x_mm == pytest.approx(geometry.x_infinity())
        assert r.marks[-1].x_mm == pytest.approx(geometry.x_mfd())


def test_mfd_label_not_duplicated_in_row():
    for unit in (Unit.METERS, Unit.FEET):
        for f in config.FOCAL_LENGTHS_MM:
            m = build_model(unit, [f])
            row = m.rows[0]
            mfd_label = row.marks[-1].label
            inter = [mk.label for mk in row.marks if mk.kind is MarkKind.INTERMEDIATE]
            assert mfd_label not in inter


def test_accepts_string_unit():
    m = build_model("meters", [75])
    assert m.unit is Unit.METERS


def test_debug_strip():
    m = build_model(None, [], debug=True)
    assert m.debug and len(m.rows) == 1
    labels = [mk.label for mk in m.rows[0].marks]
    assert labels == [str(e) for e in range(0, 15)]
    xs = [mk.x_mm for mk in m.rows[0].marks]
    assert xs == sorted(xs)
    assert xs[0] == pytest.approx(geometry.x_infinity())
    assert xs[-1] == pytest.approx(geometry.x_mfd())


def test_single_and_triple_focal():
    assert len(build_model(Unit.METERS, [75]).rows) == 1
    assert len(build_model(Unit.METERS, [50, 75, 150]).rows) == 3
