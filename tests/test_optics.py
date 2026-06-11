import math

import pytest

from scale_strip import config, optics


def test_known_mfd_values():
    # From design_docs/generator_math.md.
    assert optics.mfd_mm(75, 14) == pytest.approx(565.79, abs=0.01)
    assert optics.mfd_mm(200, 14) == pytest.approx(3271.1, abs=0.1)
    assert optics.mfd_mm(50, 14) == pytest.approx(292.57, abs=0.01)


def test_distance_at_infinity_and_inversion():
    assert math.isinf(optics.distance_mm(75, 0))
    assert optics.extension_mm(75, math.inf) == 0.0


def test_roundtrip_distance_extension():
    for f in config.FOCAL_LENGTHS_MM:
        for e in (0.5, 1.0, 3.0, 7.0, 14.0):
            d = optics.distance_mm(f, e)
            assert optics.extension_mm(f, d) == pytest.approx(e, abs=1e-6)


def test_exact_example():
    # 75mm at 5mm extension is exactly 1280mm, inverting back to 5.0.
    assert optics.distance_mm(75, 5) == 1280.0
    assert optics.extension_mm(75, 1280.0) == pytest.approx(5.0, abs=1e-9)


def test_closer_with_more_extension():
    for f in config.FOCAL_LENGTHS_MM:
        prev = math.inf
        for e in (1.0, 2.0, 5.0, 10.0, 14.0):
            d = optics.distance_mm(f, e)
            assert d < prev
            prev = d


def test_discriminant_nonnegative_across_range():
    # Every offered lens focuses across the full travel without a domain error.
    for f in config.FOCAL_LENGTHS_MM:
        d_mfd = optics.mfd_mm(f, config.EXT_MAX_MM)
        # Just inside MFD must still invert.
        assert optics.extension_mm(f, d_mfd) == pytest.approx(14.0, abs=1e-6)


def test_too_close_raises():
    with pytest.raises(ValueError):
        optics.extension_mm(75, 100.0)  # well inside 1:1
