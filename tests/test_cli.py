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


def get_parsed_peal(id: int) -> Peal:
    with open(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'parsed', f'{id}.txt'), 'r') as f:
        expected = f.read()
    return expected


def get_stored_test_data(id: int) -> Peal:
    with open(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'stored', f'{id}.txt'), 'r') as f:
        expected = f.read()
    return expected


def store_test_data(file_name: str, data: str):
    with open(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'stored', f'{file_name}.txt'), 'w') as f:
        f.write(data)


runner = CliRunner()
os.chdir(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize(
        "peal_id",
        [file.split('.')[0] for file in os.listdir(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'pages'))])
def test_peals(mock_bellboard_server, peal_id: int):
    parsed_peal = get_bellboard_peal(get_url_from_id(peal_id))
    assert str(parsed_peal) == get_parsed_peal(peal_id)


@pytest.mark.parametrize(
            'input_file',
            [file.split('.')[0] for file in sorted(os.listdir(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'stored')))])
def test_app(mock_bellboard_server, input_file: int):

    peal_id = int(input_file.split('-')[1])
    test_data = [data.strip() for data in get_stored_test_data(input_file).split('===')]
    assert len(test_data) == 4, f'Test file for peal {peal_id} doesn\'t contain 4 sections'

    result = None
    stored_peal = None
    try:
        result = runner.invoke(app,
                               test_data[0].split('|') if test_data[0] != '' else None,
                               input=test_data[1].replace('|', '\n') + '\n')
        assert result.exit_code == 0, "App exited with non-zero exit code"
        assert result.output.strip() == test_data[3].strip(), "App output does not match expected output"

        stored_peal = Peal.get(bellboard_id=peal_id)
        assert stored_peal is not None, "Unable to retrieve saved peal"
        assert str(stored_peal) == test_data[2], "Saved peal does not match expected peal"

    except AssertionError as e:
        store_test_data(input_file,
                        test_data[0] +
                        '\n===\n' +
                        test_data[1] +
                        '\n===\n' +
                        (str(stored_peal) if stored_peal else test_data[2]) +
                        '\n===\n' +
                        (result.output if result.output else test_data[3]))
        raise e
