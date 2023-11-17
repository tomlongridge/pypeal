import pytest
from pypeal import parsers

footnotes = [
    (('', 6, [6]), (None, None)),
    ((' .', 6, [6]), (None, None)),
    (('Normal footnote.', 6, [6]), (None, 'Normal footnote.')),
    (('Normal footnote.', 6, [6]), (None, 'Normal footnote.')),
    (('About a ringer: 7', 6, [6]), ([7], 'About a ringer.')),
    (('About another ringer - 1', 6, [6]), ([1], 'About another ringer.')),
    (('About two ringers: 7, 9', 6, [6]), ([7, 9], 'About two ringers.')),
    (('About three ringers: 7,9&11', 6, [6]), ([7, 9, 11], 'About three ringers.')),
    (('About three ringers: 1, 9 and 2', 6, [6]), ([1, 2, 9], 'About three ringers.')),
    (('9: About a ringer', 6, [6]), ([9], 'About a ringer.')),
    (('4-About another ringer', 6, [6]), ([4], 'About another ringer.')),
    (('1, 2: About two ringers', 6, [6]), ([1, 2], 'About two ringers.')),
    ((' 3,4and5: About three ringers', 6, [6]), ([3, 4, 5], 'About three ringers.')),
    (('6, 5 & 3: About three ringers', 6, [6]), ([3, 5, 6], 'About three ringers.')),
    (('First quarter at first attempt - 1 2 3 5 & 6.', 6, [6]), ([1, 2, 3, 5, 6], 'First quarter at first attempt.')),
    (('First quarter as conductor', 6, [3]), ([3], 'First quarter as conductor.')),
    (('First quarter for all the band', 5, [1]), ([1, 2, 3, 4, 5], 'First quarter for all the band.')),
    (('First quarter for all the band except 2.', 3, [1]), ([1, 3], 'First quarter for all the band except 2.')),
    (('First quarter for all the band apart from 1 and 2', 3, [1]), ([3], 'First quarter for all the band apart from 1 and 2.')),
    (('First quarter for all the band except for 4 and the conductor.', 5, [1]),
     ([2, 3, 5], 'First quarter for all the band except for 4 and the conductor.')),
]


@pytest.mark.parametrize('input,expected_data,', footnotes)
def test_footnote_parse(input: tuple[str, int, list[int]], expected_data: tuple[list[int], str]):
    assert parsers.parse_footnote(*input) == expected_data
