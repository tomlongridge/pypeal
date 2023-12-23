import pytest
from pypeal.method import Stage

from pypeal.parsers import parse_method_title
from pypeal.peal import Peal, Method, PealType

methods = [
    (
        'Plain Bob Triples',
        ([Method(name='Plain', classification='Bob', stage=Stage.TRIPLES, is_plain=True)], PealType.SINGLE_METHOD, None, None, None),
        'FULL_METHOD_NAME'
    ),
    (
        'Kent Treble Bob Major',
        ([Method(name='Kent', classification='Treble Bob', stage=Stage.MAJOR)], PealType.SINGLE_METHOD, None, None, None),
        'FULL_METHOD_NAME'
    ),
    (
        'Spliced Kent and Oxford Treble Bob Major',
        ([Method(name='Kent', classification='Treble Bob', stage=Stage.MAJOR),
          Method(name='Oxford', classification='Treble Bob', stage=Stage.MAJOR)],
         PealType.SPLICED_METHODS, 2, None, None),
        'Spliced Treble Bob Major (2m)'
    ),
    (
        'Bainton Treble Place Minimus',
        ([Method(name='Bainton', classification='Treble Place', stage=Stage.MINIMUS)], PealType.SINGLE_METHOD, None, None, None),
        'FULL_METHOD_NAME'
    ),
    (
        'Stedman Caters',
        ([Method(name='Stedman', stage=Stage.CATERS)], PealType.SINGLE_METHOD, None, None, None),
        'FULL_METHOD_NAME'
    ),
    (
        'Zanussi Surprise Maximus',
        ([Method(name='Zanussi', classification='Surprise', stage=Stage.MAXIMUS)], PealType.SINGLE_METHOD, None, None, None),
        'FULL_METHOD_NAME'
    ),
    (
        'Doubles (2m)',
        ([Method(stage=Stage.DOUBLES)], PealType.MIXED_METHODS, 2, 0, 0),
        'Mixed Doubles (2m)'
    ),
    (
        'Doubles (11m/v/p)',
        ([Method(stage=Stage.DOUBLES)], PealType.MIXED_METHODS, 11, 0, 0),
        'Mixed Doubles (11m)',
    ),
    (
        'Doubles',
        ([Method(stage=Stage.DOUBLES)], PealType.MIXED_METHODS, None, None, None),
        'Mixed Doubles',
    ),
    (
        'Mixed Doubles (3m/1p/2v)',
        ([Method(stage=Stage.DOUBLES)], PealType.MIXED_METHODS, 3, 2, 1),
        'Mixed Doubles (3m/2v/1p)'
    ),
    (
        'Doubles 2m',
        ([Method(stage=Stage.DOUBLES)], PealType.MIXED_METHODS, 2, 0, 0),
        'Mixed Doubles (2m)'
    ),
    (
        '6 Minor',
        ([Method(stage=Stage.MINOR)], PealType.SPLICED_METHODS, 6, None, None),
        'Spliced Minor (6m)'
    ),
    (
        '3 Surprise Major',
        ([Method(stage=Stage.MAJOR, classification='Surprise')], PealType.SPLICED_METHODS, 3, None, None),
        'Spliced Surprise Major (3m)'
    ),
    (
        'Spliced Surprise Minor (8m)',
        ([Method(classification='Surprise', stage=Stage.MINOR)], PealType.SPLICED_METHODS, 8, 0, 0),
        None
    ),
    (
        'Rounds',
        ([Method(name='Rounds')], PealType.GENERAL_RINGING, None, None, None),
        'FULL_METHOD_NAME'
    ),
    (
        'Spliced Cambridge and Yorkshire Surprise Major',
        ([Method(name='Cambridge', classification='Surprise', stage=Stage.MAJOR),
          Method(name='Yorkshire', classification='Surprise', stage=Stage.MAJOR)], PealType.SPLICED_METHODS, 2, None, None),
        'Spliced Surprise Major (2m)'
    ),
    (
        'Spliced Cambridge Surprise and Yorkshire Surprise Major',
        ([Method(name='Cambridge', classification='Surprise', stage=Stage.MAJOR),
          Method(name='Yorkshire', classification='Surprise', stage=Stage.MAJOR)], PealType.SPLICED_METHODS, 2, None, None),
        'Spliced Surprise Major (2m)'
    ),
    (
        'Spliced Cambridge Surprise Major and Yorkshire Surprise Major',
        ([Method(name='Cambridge', classification='Surprise', stage=Stage.MAJOR),
          Method(name='Yorkshire', classification='Surprise', stage=Stage.MAJOR)], PealType.SPLICED_METHODS, 2, None, None),
        'Spliced Surprise Major (2m)'
    ),
    (
        'Spliced Cambridge Delight Royal and Grandsire Caters',
        ([Method(name='Cambridge', classification='Delight', stage=Stage.ROYAL),
          Method(name='Grandsire', stage=Stage.CATERS)], PealType.SPLICED_METHODS, 2, None, None),
        'Spliced Caters and Royal (2m)'
    ),
    (
        'Stedman and Grandsire Triples',
        ([Method(name='Stedman', stage=Stage.TRIPLES),
          Method(name='Grandsire', stage=Stage.TRIPLES)], PealType.SPLICED_METHODS, 2, None, None),
        'Spliced Triples (2m)'
    ),
    (
        'St Simons and St Martins Triples',
        ([Method(name='St Simons', stage=Stage.TRIPLES),
          Method(name='St Martins', stage=Stage.TRIPLES)], PealType.SPLICED_METHODS, 2, None, None),
        'Spliced Triples (2m)'
    )
]


@pytest.mark.parametrize('title,expected_details,expected_title', methods)
def test_parse_method_title(title: str, expected_details: tuple[list[Method], PealType, int, int, int], expected_title: str):
    method_details: tuple[list[Method], PealType, int, int, int] = parse_method_title(title)
    assert method_details == expected_details
    methods, peal_type, num_methods, num_variants, num_principles = method_details
    peal = Peal(1)
    if len(methods) == 1:
        methods[0].full_name = 'FULL_METHOD_NAME'  # The real method will have a full name used in peal.title
        peal.method = methods[0]
        peal.stage = methods[0].stage
        peal.classification = methods[0].classification
    elif len(methods) == 2:
        methods[0].full_name = 'FULL_METHOD_NAME_1'
        methods[1].full_name = 'FULL_METHOD_NAME_2'
        peal.stage = methods[0].stage
        if methods[0].stage != methods[1].stage:
            peal.is_variable_cover = True
        if methods[0].classification == methods[1].classification:
            peal.classification = methods[0].classification
    else:
        raise AssertionError('Unexpected number of methods')
    peal.type = peal_type
    if peal_type in [PealType.MIXED_METHODS, PealType.SPLICED_METHODS]:
        peal.method = None

    peal.num_methods = num_methods
    peal.num_variants = num_variants
    peal.num_principles = num_principles
    assert peal.title == (expected_title if expected_title else title)
