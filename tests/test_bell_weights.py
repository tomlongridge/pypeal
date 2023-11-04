import pytest
from pypeal import parsers


from pypeal.utils import get_weight_str

weights = [
    (None, None, 'Unknown'),
    ('0-0-1', 1, None),
    ('0-0-27', 27, None),
    ('0-1-0', 28, None),
    ('0-1-1', 29, None),
    ('0-3-27', 111, None),
    ('1 cwt', 112, None),
    ('1', 112, '1 cwt'),
    ('1-0-1', 113, None),
    ('2 cwt', 224, None),
    ('17-2-15', 1975, None),
]


@pytest.mark.parametrize('input_str,lbs,expected_str,', weights)
def test_bell_weights(input_str: str, lbs: int, expected_str: str):
    assert parsers.parse_bell_weight(input_str) == lbs
    assert get_weight_str(lbs) == (expected_str if expected_str else input_str)
