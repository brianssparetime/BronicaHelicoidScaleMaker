import pytest

from scale_strip import config, geometry
from scale_strip.marks import _slot_bands, candidate_values, select_marks
from scale_strip.model import _slots
from scale_strip.units import Unit

_FOCALS = [40, 50, 75, 100, 150, 200]


def _valid_label_value(value, unit):
    step = 2.0 if unit is Unit.FEET else 10.0
    return abs(value * step - round(value * step)) < 1e-9


@pytest.mark.parametrize("unit", [Unit.FEET, Unit.METERS])
@pytest.mark.parametrize("f", _FOCALS)
def test_marks_obey_number_rules(unit, f):
    for m in select_marks(f, unit, 0.0, _slots()):
        assert _valid_label_value(m.value, unit), (f, unit, m.value)


@pytest.mark.parametrize("unit", [Unit.FEET, Unit.METERS])
@pytest.mark.parametrize("f", _FOCALS)
def test_marks_within_active_scale(unit, f):
    x_inf, x_mfd = geometry.x_infinity(), geometry.x_mfd()
    for m in select_marks(f, unit, 0.0, _slots()):
        assert x_inf < m.x_mm < x_mfd


@pytest.mark.parametrize("unit", [Unit.FEET, Unit.METERS])
@pytest.mark.parametrize("f", _FOCALS)
def test_marks_avoid_slots(unit, f):
    bands = _slot_bands(_slots())
    for m in select_marks(f, unit, 0.0, _slots()):
        for lo, hi in bands:
            assert not (lo <= m.x_mm <= hi), (f, unit, m.x_mm)


@pytest.mark.parametrize("unit", [Unit.FEET, Unit.METERS])
@pytest.mark.parametrize("f", _FOCALS)
def test_marks_respect_minimum_gap(unit, f):
    xs = [m.x_mm for m in select_marks(f, unit, 0.0, _slots())]
    for a, b in zip(xs, xs[1:]):
        assert b - a >= config.MIN_MARK_GAP_MM - 1e-6


def test_candidate_values_meters_one_decimal():
    for value, _ in candidate_values(Unit.METERS, 0.2, 100):
        assert _valid_label_value(value, Unit.METERS)
    # 0.15 and 0.25 violate the one-decimal rule and must not appear.
    values = {v for v, _ in candidate_values(Unit.METERS, 0.1, 100)}
    assert 0.15 not in values and 0.25 not in values


def test_candidate_values_feet_whole_or_half():
    for value, _ in candidate_values(Unit.FEET, 1, 200):
        assert _valid_label_value(value, Unit.FEET)
    values = {v for v, _ in candidate_values(Unit.FEET, 0.1, 50)}
    assert 0.2 not in values and 0.3 not in values
