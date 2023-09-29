import os
from typer.testing import CliRunner

import pytest
from xprocess import ProcessStarter, XProcess

from pypeal.peal import Peal
from pypeal.cli.app import app

runner = CliRunner()


@pytest.fixture
def mock_bellboard_server(xprocess: XProcess):
    class Starter(ProcessStarter):
        # Startup command
        args = ['python', os.path.join(os.path.dirname(__file__), 'scripts', 'server.py')]
        # String to look for on startup
        pattern = 'Mock server started'

    xprocess.ensure("mock_bellboard_server", Starter)
    yield
    xprocess.getinfo("mock_bellboard_server").terminate()


def get_expected_peal(id: int) -> Peal:
    with open(f'tests/files/peals/stored/{id}.txt', 'r') as f:
        expected = f.read()
    return expected


def test_app(mock_bellboard_server):
    result = runner.invoke(app,
                           ['--reset-database'],
                           input='1\n22152\n\n\n\n\n\n\n\n\n3\n',
                           env={'PYPEAL_CONFIG': 'tests/files/test_config.ini'})
    assert result.exit_code == 0
    stored_peal = Peal.get(bellboard_id=22152)
    assert stored_peal is not None
    print(stored_peal)
    assert str(stored_peal) == get_expected_peal(22152)
