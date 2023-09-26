import pytest
import os

import sys
sys.path.append('src')
import pypeal.bellboard  # noqa: E402

peals = []
for file in os.listdir('tests/peals/pages'):
    id = int(file.split('.')[0])
    with open(f'tests/peals/pages/{id}.html', 'r') as f:
        html = f.read()
    
    with open(f'tests/peals/parsed/{id}.txt', 'r') as f:
        expected = f.read()
    peals += [(id, html, expected)]


@pytest.mark.parametrize("peal_id,html,expected", peals, ids=[str(peal[0]) for peal in peals])
def test_peals(peal_id: int, html: str, expected: str):
    peal = pypeal.bellboard.get_peal(peal_id, html)
    assert str(peal) == expected
