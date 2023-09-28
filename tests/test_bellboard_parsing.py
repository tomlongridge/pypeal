import pytest
import os

import sys
sys.path.append('../pypeal')
import pypeal.bellboard  # noqa: E402

peals = []
for file in os.listdir(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'pages')):
    id = int(file.split('.')[0])
    with open(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'pages', file), 'r') as f:
        html = f.read()

    with open(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'parsed', f'{id}.txt'), 'r') as f:
        expected = f.read()
    peals += [(id, html, expected)]


@pytest.mark.parametrize("peal_id,html,expected", peals, ids=[str(peal[0]) for peal in peals])
def test_peals(peal_id: int, html: str, expected: str):
    peal = pypeal.bellboard.get_peal(html=html)
    assert str(peal) == expected
