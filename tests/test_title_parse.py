import pytest
from pypeal.method import Stage

from pypeal.parsers import parse_method_title
from pypeal.peal import Peal, Method

methods = [
    (
        'Plain Bob Triples',
        (Method(name='Plain', classification='Bob', stage=Stage.TRIPLES), False, None, None, None, None),
        None
    ),
    (
        'Kent Treble Bob Major',
        (Method(name='Kent', classification='Treble Bob', stage=Stage.MAJOR), False, None, None, None, None),
        None
    ),
    (
        'Kent and Oxford Treble Bob Major',
        (Method(name='Kent and Oxford', classification='Treble Bob', stage=Stage.MAJOR), False, None, None, None, None),
        None
    ),
    (
        'Bainton Treble Place Minimus',
        (Method(name='Bainton', classification='Treble Place', stage=Stage.MINIMUS), False, None, None, None, None),
        None
    ),
    (
        'Stedman Caters',
        (Method(name='Stedman', stage=Stage.CATERS), False, None, None, None, None),
        None
    ),
    (
        'Zanussi Surprise Maximus',
        (Method(name='Zanussi', classification='Surprise', stage=Stage.MAXIMUS), False, None, None, None, None),
        None
    ),
    (
        'Doubles (2m)',
        (Method(stage=Stage.DOUBLES), False, True, 2, 0, 0),
        'Mixed Doubles (2m)'
    ),
    (
        'Doubles (11m/v/p)',
        (Method(stage=Stage.DOUBLES), False, True, 11, 0, 0),
        'Mixed Doubles (11m)',
    ),
    (
        'Doubles',
        (Method(stage=Stage.DOUBLES), False, True, None, None, None),
        'Mixed Doubles',
    ),
    (
        'Mixed Doubles (3m/1p/2v)',
        (Method(stage=Stage.DOUBLES), False, True, 3, 2, 1),
        'Mixed Doubles (3m/2v/1p)'
    ),
    (
        'Spliced Surprise Minor (8m)',
        (Method(classification='Surprise', stage=Stage.MINOR), True, False, 8, 0, 0),
        None
    ),
    (
        'Rounds',
        (Method(name='Rounds'), False, None, None, None, None),
        None
    ),
]


@pytest.mark.parametrize('title,expected_details,expected_title', methods)
def test_parse_method_title(title: str, expected_details: tuple[Method, bool, bool, int, int, int], expected_title: str):
    method_details: tuple[Method, bool, bool, int, int, int] = parse_method_title(title)
    assert method_details == expected_details
    method, is_spliced, is_mixed, num_methods, num_variants, num_principles = method_details
    peal = Peal(1)
    peal.method = method
    peal.is_spliced = is_spliced
    peal.is_mixed = is_mixed
    peal.stage = method.stage
    peal.classification = method.classification
    peal.num_methods = num_methods
    peal.num_variants = num_variants
    peal.num_principles = num_principles
    assert peal.method_title == expected_title if expected_title else title
