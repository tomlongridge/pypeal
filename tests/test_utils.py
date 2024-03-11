from pypeal.utils import get_time_str


def test_get_time_str_with_zero_minutes():
    assert get_time_str(0) == '0m'
    assert get_time_str(0, full=True) == '0 mins'


def test_get_time_str_less_than_minute():
    assert get_time_str(0.75) == '45s'
    assert get_time_str(0.75, full=True) == '45 secs'


def test_get_time_str_with_float_minutes():
    assert get_time_str(1.5) == '1m 30s'
    assert get_time_str(1.5, full=True) == '1 min, 30 secs'


def test_get_time_str_with_minutes_only():
    assert get_time_str(45) == '45m'
    assert get_time_str(45, full=True) == '45 mins'


def test_get_time_str_with_hours_and_minutes():
    assert get_time_str(75) == '1h 15m'
    assert get_time_str(75, full=True) == '1 hour, 15 mins'
    assert get_time_str(125) == '2h 5m'
    assert get_time_str(125, full=True) == '2 hours, 5 mins'


def test_get_time_str_with_days_hours_and_minutes():
    assert get_time_str(1550) == '1d 1h 50m'
    assert get_time_str(1550, full=True) == '1 day, 1 hour, 50 mins'
    assert get_time_str(3550) == '2d 11h 10m'
    assert get_time_str(3550, full=True) == '2 days, 11 hours, 10 mins'


def test_get_time_str_with_none():
    assert get_time_str(None) == 'Unknown'
    assert get_time_str(None, full=True) == 'Unknown'
