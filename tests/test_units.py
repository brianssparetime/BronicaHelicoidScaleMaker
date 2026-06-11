from scale_strip.units import Unit, format_distance, format_mfd, from_mm, to_mm


def test_feet_format_whole_and_half():
    assert format_distance(5.0, Unit.FEET) == "5"
    assert format_distance(1.5, Unit.FEET) == "1.5"
    assert format_distance(10.0, Unit.FEET) == "10"


def test_meters_format_one_decimal():
    assert format_distance(0.5, Unit.METERS) == "0.5"
    assert format_distance(3.0, Unit.METERS) == "3"
    assert format_distance(1.5, Unit.METERS) == "1.5"


def test_mfd_keeps_true_value():
    # MFD is exempt from the round-number rules; it shows the true distance.
    assert format_mfd(0.566) == "0.57"
    assert format_mfd(0.293) == "0.29"
    assert format_mfd(1.921) == "1.92"
    assert format_mfd(10.73) == "10.7"   # one decimal above ten
    assert format_mfd(6.30) == "6.3"


def test_unit_conversion_roundtrip():
    for unit in (Unit.FEET, Unit.METERS):
        assert from_mm(to_mm(3.0, unit), unit) == 3.0
