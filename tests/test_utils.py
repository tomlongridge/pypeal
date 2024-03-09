from pypeal.utils import get_time_str


def test_get_time_str_with_zero_minutes():
    assert get_time_str(0) == '0 mins'


def test_get_time_str_less_than_minute():
    assert get_time_str(0.75) == '45 secs'


def test_get_time_str_with_float_minutes():
    assert get_time_str(1.5) == '1 min, 30 secs'


def test_get_time_str_with_minutes_only():
    assert get_time_str(45) == '45 mins'


def test_get_time_str_with_hours_and_minutes():
    assert get_time_str(75) == '1 hour, 15 mins'
    assert get_time_str(125) == '2 hours, 5 mins'


def test_get_time_str_with_days_hours_and_minutes():
    assert get_time_str(1550) == '1 day, 1 hour, 50 mins'
    assert get_time_str(3550) == '2 days, 11 hours, 10 mins'


def test_get_time_str_with_none():
    assert get_time_str(None) == 'Unknown'
