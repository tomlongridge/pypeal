import pytest
from pypeal import parsers


names = [
    (None, None),
    ('Smith', ('Smith', None, None)),
    ('John Smith', ('Smith', 'John', None)),
    ('John Smith-Johnson', ('Smith-Johnson', 'John', None)),
    ('John Paul Smith', ('Smith', 'John Paul', None)),
    ('Rev John Paul Smith', ('Smith', 'John Paul', 'Rev')),
    ('Revd. John Paul Smith', ('Smith', 'John Paul', 'Revd')),
]


@pytest.mark.parametrize('input_str,expected_names', names)
def test_name_parse(input_str: str, expected_names: tuple[str, str, str]):
    assert parsers.parse_ringer_name(input_str) == expected_names
