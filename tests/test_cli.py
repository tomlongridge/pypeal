import os
from typer.testing import CliRunner

import pytest
from xprocess import ProcessStarter, XProcess

import sys
sys.path.append('../pypeal')
from pypeal.peal import Peal  # noqa: E402
from pypeal.cli.app import app  # noqa: E402
from pypeal.bellboard import get_peal as get_bellboard_peal, get_url_from_id  # noqa: E402


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


def run_cli(input: list[str]):
    result = runner.invoke(app,
                           ['--reset-database'],
                           input='\n'.join(input) + '\n')
    print(result.stdout)
    assert result.exit_code == 0


def get_parsed_peal(id: int) -> Peal:
    with open(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'parsed', f'{id}.txt'), 'r') as f:
        expected = f.read()
    return expected


def get_stored_peal(id: int) -> Peal:
    with open(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'stored', f'{id}.txt'), 'r') as f:
        expected = f.read()
    return expected


runner = CliRunner()
os.chdir(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize(
        "peal_id",
        [file.split('.')[0] for file in os.listdir(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'pages'))])
def test_peals(mock_bellboard_server, peal_id: int):
    parsed_peal = get_bellboard_peal(get_url_from_id(peal_id))
    assert str(parsed_peal) == get_parsed_peal(peal_id)


# @pytest.mark.parametrize(
#         "peal_id",
#         [file.split('.')[0] for file in os.listdir(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'pages'))])
# def test_app(mock_bellboard_server, peal_id: int):
#     run_cli(['1', str(peal_id), '', '', '', '', '', '', '', ''])
#     stored_peal = Peal.get(bellboard_id=peal_id)
#     assert stored_peal is not None
#     assert str(stored_peal) == get_stored_peal(peal_id)

@pytest.mark.parametrize(
            "peal_id,input",
            [
                (22152, ['1', '22152', '', '', '', '', '', '', '', '', '3']),
                (1306360, ['1', '1306360', '', '', '', '', '', '', '3']),
                (1346767, ['1', '1346767', '', '', '', '', '', '', '3']),
                (1425962, ['1', '1425962', '', '', '', '', '', '', '', '', '3']),
                (1426065, ['1', '1426065', '', '', '', '', '', '', '', '', '3']),
                (1426139, ['1', '1426139', '', '', '', '', '', '', '', '', '', '', '3']),
                (1433691, ['1', '1433691', '', '', '', '', '', '', '3']),
                (1508383, ['1', '1508383', '', '', '', '', '', '', '3']),
                (1627555, ['1', '1627555', '', '', '', '', '', '', '', '', '3']),
            ]
        )
def test_app(mock_bellboard_server, peal_id: int, input: list[str]):
    run_cli(input)
    stored_peal = Peal.get(bellboard_id=peal_id)
    assert stored_peal is not None
    print(stored_peal)
    assert str(stored_peal) == get_stored_peal(peal_id)
