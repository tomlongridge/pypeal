import pytest
from pypeal.method import Stage

from pypeal.parsers import parse_method_title
from pypeal.peal import Peal, Method, PealType

methods = [
    (
        'Plain Bob Triples',
        ([Method(name='Plain', classification='Bob', stage=Stage.TRIPLES, is_plain=True)], False, None, None, None, None),
        None
    ),
    (
        'Kent Treble Bob Major',
        ([Method(name='Kent', classification='Treble Bob', stage=Stage.MAJOR)], False, None, None, None, None),
        None
    ),
    (
        'Spliced Kent and Oxford Treble Bob Major',
        ([Method(name='Kent', classification='Treble Bob', stage=Stage.MAJOR),
          Method(name='Oxford', classification='Treble Bob', stage=Stage.MAJOR)], 
         True, False, 2, None, None),
        'Spliced Treble Bob Major (2m)'
    ),
    (
        'Bainton Treble Place Minimus',
        ([Method(name='Bainton', classification='Treble Place', stage=Stage.MINIMUS)], False, None, None, None, None),
        None
    ),
    (
        'Stedman Caters',
        ([Method(name='Stedman', stage=Stage.CATERS)], False, None, None, None, None),
        None
    ),
    (
        'Zanussi Surprise Maximus',
        ([Method(name='Zanussi', classification='Surprise', stage=Stage.MAXIMUS)], False, None, None, None, None),
        None
    ),
    (
        'Doubles (2m)',
        ([Method(stage=Stage.DOUBLES)], False, True, 2, 0, 0),
        'Mixed Doubles (2m)'
    ),
    (
        'Doubles (11m/v/p)',
        ([Method(stage=Stage.DOUBLES)], False, True, 11, 0, 0),
        'Mixed Doubles (11m)',
    ),
    (
        'Doubles',
        ([Method(stage=Stage.DOUBLES)], False, True, None, None, None),
        'Mixed Doubles',
    ),
    (
        'Mixed Doubles (3m/1p/2v)',
        ([Method(stage=Stage.DOUBLES)], False, True, 3, 2, 1),
        'Mixed Doubles (3m/2v/1p)'
    ),
    (
        'Doubles 2m',
        ([Method(stage=Stage.DOUBLES)], False, True, 2, 0, 0),
        'Mixed Doubles (2m)'
    ),
    (
        '6 Minor',
        ([Method(stage=Stage.MINOR)], False, True, 6, None, None),
        'Mixed Minor (6m)'
    ),
    (
        '3 Surprise Major',
        ([Method(stage=Stage.MAJOR, classification='Surprise')], False, True, 3, None, None),
        'Mixed Surprise Major (3m)'
    ),
    (
        'Spliced Surprise Minor (8m)',
        ([Method(classification='Surprise', stage=Stage.MINOR)], True, False, 8, 0, 0),
        None
    ),
    (
        'Rounds',
        ([Method(name='Rounds')], False, None, None, None, None),
        None
    ),
    (
        'Spliced Cambridge and Yorkshire Surprise Major',
        ([Method(name='Cambridge', classification='Surprise', stage=Stage.MAJOR),
          Method(name='Yorkshire', classification='Surprise', stage=Stage.MAJOR)], True, False, 2, None, None),
        'Spliced Surprise Major (2m)'
    ),
    (
        'Spliced Cambridge Surprise and Yorkshire Surprise Major',
        ([Method(name='Cambridge', classification='Surprise', stage=Stage.MAJOR),
          Method(name='Yorkshire', classification='Surprise', stage=Stage.MAJOR)], True, False, 2, None, None),
        'Spliced Surprise Major (2m)'
    ),
    (
        'Spliced Cambridge Surprise Major and Yorkshire Surprise Major',
        ([Method(name='Cambridge', classification='Surprise', stage=Stage.MAJOR),
          Method(name='Yorkshire', classification='Surprise', stage=Stage.MAJOR)], True, False, 2, None, None),
        'Spliced Surprise Major (2m)'
    ),
    (
        'Spliced Cambridge Delight Royal and Grandsire Caters',
        ([Method(name='Cambridge', classification='Delight', stage=Stage.ROYAL),
          Method(name='Grandsire', stage=Stage.CATERS)], True, False, 2, None, None),
        'Spliced Caters and Royal (2m)'
    ),
    (
        'Stedman and Grandsire Triples',
        ([Method(name='Stedman', stage=Stage.TRIPLES),
          Method(name='Grandsire', stage=Stage.TRIPLES)], False, True, 2, None, None),
        'Mixed Triples (2m)'
    )
]


@pytest.mark.parametrize('title,expected_details,expected_title', methods)
def test_parse_method_title(title: str, expected_details: tuple[list[Method], bool, bool, int, int, int], expected_title: str):
    method_details: tuple[list[Method], bool, bool, int, int, int] = parse_method_title(title)
    assert method_details == expected_details
    methods, is_spliced, is_mixed, num_methods, num_variants, num_principles = method_details
    peal = Peal(1)
    if len(methods) == 1:
        peal.method = methods[0]
        peal.stage = methods[0].stage
        peal.classification = methods[0].classification
    elif len(methods) == 2:
        peal.stage = methods[0].stage
        if methods[0].stage != methods[1].stage:
            peal.is_variable_cover = True
        if methods[0].classification == methods[1].classification:
            peal.classification = methods[0].classification
    if is_spliced:
        peal.type = PealType.SPLICED_METHODS
        peal.method = None
    elif is_mixed:
        peal.type = PealType.MIXED_METHODS
        peal.method = None

    peal.num_methods = num_methods
    peal.num_variants = num_variants
    peal.num_principles = num_principles
    assert peal.title == (expected_title if expected_title else title)
