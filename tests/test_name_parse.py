import pytest
from pypeal import parsers


names = [
    (None, None),
    ('Smith', ('Smith', None, None, None)),
    ('John Smith', ('Smith', 'John', None, None)),
    ('John Smith-Johnson', ('Smith-Johnson', 'John', None, None)),
    ('John Paul Smith', ('Smith', 'John Paul', None, None)),
    ('Rev John Paul Smith', ('Smith', 'John Paul', 'Rev', None)),
    ('Revd. John Paul Smith', ('Smith', 'John Paul', 'Revd', None)),
    ('Smith (Captain)', ('Smith', None, None, 'Captain')),
    ('John Smith (Captain)', ('Smith', 'John', None, 'Captain')),
    ('John Smith-Johnson (Captain)', ('Smith-Johnson', 'John', None, 'Captain')),
    ('John Paul Smith (Captain)', ('Smith', 'John Paul', None, 'Captain')),
    ('Rev John Paul Smith (Captain)', ('Smith', 'John Paul', 'Rev', 'Captain')),
    ('Revd. John Paul Smith (Captain)', ('Smith', 'John Paul', 'Revd', 'Captain')),
]


@pytest.mark.parametrize('input_str,expected_names', names)
def test_name_parse(input_str: str, expected_names: tuple[str, str, str]):
    assert parsers.parse_ringer_name(input_str) == expected_names
