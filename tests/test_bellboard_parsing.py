import pytest
import os

import sys
sys.path.append('src')
from pypeal.bellboard import BellboardSearcher  # noqa: E402

peals = []
for file in os.listdir('tests/peals/pages'):
    id = int(file.split('.')[0])
    with open(f'tests/peals/pages/{id}.html', 'r') as f:
        html = f.read()
    peal = BellboardSearcher().get_peal(id, html)
    with open(f'tests/peals/parsed/{id}.txt', 'r') as f:
        expected = f.read()
    peals += [(str(peal), expected)]


@pytest.mark.parametrize("test_input,expected", peals)
def test_peals(test_input, expected):
    assert test_input == expected
