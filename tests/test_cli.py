import os
import pathlib
import pytest
from xprocess import ProcessStarter, XProcess

from pypeal.cli.app import app
from tests.scripts.runner import cli_runner


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


os.chdir(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize(
    'input_file',
    [str(filepath.absolute())
     for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'stored')).glob('*.txt'))],
    ids=[filepath.name.split('.')[0]
         for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'stored')).glob('*.txt'))])
def test_bellboard_import(mock_bellboard_server, input_file: int):
    cli_runner(app, input_file)


@pytest.mark.parametrize(
    'input_file',
    [str(filepath.absolute())
     for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'new')).glob('*.txt'))],
    ids=[filepath.name.split('.')[0]
         for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'new')).glob('*.txt'))])
def test_new_peals(mock_bellboard_server, input_file: int):
    cli_runner(app, input_file)
