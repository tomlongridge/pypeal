import pytest
from pypeal import parsers

footnotes = [
    ('', (None, None)),
    (' .', (None, None)),
    ('Normal footnote.', (None, 'Normal footnote.')),
    ('Normal footnote.', (None, 'Normal footnote.')),
    ('About a ringer: 7', ([7], 'About a ringer.')),
    ('About another ringer - 1', ([1], 'About another ringer.')),
    ('About two ringers: 7, 9', ([7, 9], 'About two ringers.')),
    ('About three ringers: 7,9&11', ([7, 9, 11], 'About three ringers.')),
    ('About three ringers: 1, 9 and 2', ([1, 2, 9], 'About three ringers.')),
    ('9: About a ringer', ([9], 'About a ringer.')),
    ('4-About another ringer', ([4], 'About another ringer.')),
    ('1, 2: About two ringers', ([1, 2], 'About two ringers.')),
    (' 3,4and5: About three ringers', ([3, 4, 5], 'About three ringers.')),
    ('6, 5 & 3: About three ringers', ([3, 5, 6], 'About three ringers.')),
]


@pytest.mark.parametrize('input_str,expected_data,', footnotes)
def test_footnote_parse(input_str: str, expected_data: tuple[list[int], str]):
    assert parsers.parse_footnote(input_str) == expected_data
