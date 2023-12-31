import os
import pytest
from xprocess import ProcessStarter, XProcess
from typer.testing import CliRunner
from click.testing import Result

from pypeal.peal import Peal
from pypeal.cli.app import app


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
    'input_file',
    [file.split('.')[0] for file in sorted(os.listdir(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'stored')))])
def test_app(mock_bellboard_server, input_file: int):

    peal_ids = [int(peal_id) for peal_id in input_file.split('-')[1].split('|')]
    test_data = [data.strip() for data in get_stored_test_data(input_file).split('===')]
    assert len(test_data) >= 3, f'Test file for peal {input_file} doesn\'t contain at least 3 sections'

    stdin: list[str] = []
    expected_stdout = ''
    for line in test_data[1].split('\n'):
        if line.startswith('>>>'):
            stdin.append(line[3:].strip())
        else:
            expected_stdout += line + '\n'
    expected_stdout = expected_stdout.strip()

    result: Result = None
    stored_peals = []
    test_output = ''
    try:
        result = runner.invoke(app,
                               test_data[0].split('|') if test_data[0] != '' else None,
                               input='\n'.join(stdin) + '\n')

        for line in result.output.split('\n'):
            if line.startswith('[User input:') and len(stdin) > 0:
                test_output += '>>> ' + stdin.pop(0) + '\n'
            test_output += line + '\n'
        for remaining_input in stdin:
            test_output += '>>> ' + remaining_input + '\n'

        if result.exception and type(result.exception) is not SystemExit:
            raise result.exception

        stored_peals: list[Peal] = [Peal.get(bellboard_id=id) for id in peal_ids]

        assert result.output.strip() == expected_stdout, "App output does not match expected output"
        assert result.exit_code == 0, "App exited with non-zero exit code"
        assert len(stored_peals) == len(test_data[2:]), "Unable to retrieve saved peals"
        for stored, expected in zip(stored_peals, test_data[2:]):
            assert str(stored) == expected, "Saved peal does not match expected peal"

    except Exception as e:
        store_test_data(input_file,
                        test_data[0] +
                        '\n===\n' +
                        test_output.strip() +
                        '\n===\n' +
                        '\n===\n'.join(map(lambda p: str(p), stored_peals)))
        raise e
