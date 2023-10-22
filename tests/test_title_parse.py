import pytest

from pypeal.parsers import parse_method_title
from pypeal.peal import Peal

methods = [
    (
        'Plain Bob Triples',
        Peal(1, title='Plain', classification='Bob', stage=7, is_spliced=False),
        None
    ),
    (
        'Kent Treble Bob Major',
        Peal(1, title='Kent', classification='Treble Bob', stage=8, is_spliced=False),
        None
    ),
    (
        'Kent and Oxford Treble Bob Major',
        Peal(1, title='Kent and Oxford', classification='Treble Bob', stage=8, is_spliced=False),
        None
    ),
    (
        'Bainton Treble Place Minimus',
        Peal(1, title='Bainton', classification='Treble Place', stage=4, is_spliced=False),
        None
    ),
    (
        'Stedman Caters',
        Peal(1, title='Stedman', stage=9, is_spliced=False),
        None
    ),
    (
        'Zanussi Surprise Maximus',
        Peal(1, title='Zanussi', classification='Surprise', stage=12, is_spliced=False),
        None
    ),
    (
        'Doubles (2m)',
        Peal(1, stage=5, num_methods=2, is_mixed=True, is_spliced=False),
        'Mixed Doubles (2m)'
    ),
    (
        'Doubles (11m/v/p)',
        Peal(1, stage=5, num_methods=11, is_mixed=True, is_spliced=False),
        'Mixed Doubles (11m)',
    ),
    (
        'Doubles',
        Peal(1, stage=5, is_mixed=True, is_spliced=False),
        'Mixed Doubles',
    ),
    (
        'Mixed Doubles (3m/1p/2v)',
        Peal(1, stage=5, num_methods=3, num_principles=1, num_variants=2, is_mixed=True, is_spliced=False),
        'Mixed Doubles (3m/2v/1p)'
    ),
    (
        'Spliced Surprise Minor (8m)',
        Peal(1, stage=6, classification='Surprise', num_methods=8, is_spliced=True),
        None
    ),
    (
        'Rounds',
        Peal(1, title='Rounds', is_spliced=False),
        None
    ),
]


@pytest.mark.parametrize('title,expected_peal,expected_title', methods)
def test_parse_method_title(title: str, expected_peal: Peal, expected_title: str):
    peal = Peal(1)
    parse_method_title(title, peal)
    assert peal == expected_peal
    assert peal.method_title == expected_title if expected_title else title
