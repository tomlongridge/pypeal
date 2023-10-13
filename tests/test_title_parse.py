import pytest

from pypeal.bellboard import parse_method_title
from pypeal.method import Stage
from pypeal.peal import Peal


@pytest.fixture
def peal():
    return Peal(1)


@pytest.mark.parametrize('title,expected_peal',
                         [
                            ('Plain Bob Triples',
                                Peal(1, title='Plain', classification='Bob', stage=7, is_spliced=False)),
                            ('Kent Treble Bob Major',
                                Peal(1, title='Kent', classification='Treble Bob', stage=8, is_spliced=False)),
                            ('Kent and Oxford Treble Bob Major',
                                Peal(1, title='Kent and Oxford', classification='Treble Bob', stage=8, is_spliced=False)),
                            ('Bainton Treble Place Minimus',
                                Peal(1, title='Bainton', classification='Treble Place', stage=4, is_spliced=False)),
                            ('Stedman Caters',
                                Peal(1, title='Stedman', stage=9, is_spliced=False)),
                            ('Zanussi Surprise Maximus',
                                Peal(1, title='Zanussi', classification='Surprise', stage=12, is_spliced=False)),
                            ('Doubles (2m)',
                                Peal(1, stage=5, num_methods=2, is_mixed=True, is_spliced=False)),
                            ('Doubles (11m/v/p)',
                                Peal(1, stage=5, num_methods=11, is_mixed=True, is_spliced=False)),
                            ('Doubles',
                                Peal(1, stage=5, is_mixed=True, is_spliced=False)),
                            ('Mixed Doubles (3m/1p/2v)',
                                Peal(1, stage=5, num_methods=3, num_principles=1, num_variants=2, is_mixed=True, is_spliced=False)),
                            ('Spliced Surprise Minor (8m)',
                                Peal(1, stage=6, classification='Surprise', num_methods=8, is_spliced=True)),
                            ('Rounds',
                                Peal(1, title='Rounds', is_spliced=False)),
                         ]
                         )
def test_method_title(peal: Peal, title: str, expected_peal: Peal):
    parse_method_title(title, peal)
    assert peal == expected_peal
