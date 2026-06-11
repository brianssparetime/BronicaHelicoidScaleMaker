import pytest

from scale_strip import config, geometry


def test_anchor_positions():
    assert geometry.x_infinity() == pytest.approx(config.INF_OFFSET_MM)
    assert geometry.x_mfd() == pytest.approx(config.INF_OFFSET_MM + config.L_SCALE_MM)


def test_extension_to_position_is_linear():
    x0 = geometry.x_from_extension(0)
    x_full = geometry.x_from_extension(config.EXT_MAX_MM)
    half = geometry.x_from_extension(config.EXT_MAX_MM / 2)
    assert x0 == pytest.approx(geometry.x_infinity())
    assert x_full == pytest.approx(geometry.x_mfd())
    assert half == pytest.approx((x0 + x_full) / 2)


def test_position_roundtrip():
    for e in (0.0, 1.0, 5.0, 9.3, 14.0):
        assert geometry.extension_from_x(geometry.x_from_extension(e)) == pytest.approx(e)
