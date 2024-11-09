import os
import pathlib
import pytest
import shutil
from xprocess import ProcessStarter, XProcess

from pypeal.cli.app import app
from tests.scripts.runner import cli_runner, set_search_results


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
    set_search_results(None)


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
     for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'individual')).glob('*.txt'))],
    ids=[filepath.name.split('.')[0]
         for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'individual')).glob('*.txt'))])
def test_bellboard_import_individual(mock_bellboard_server, input_file: int):
    cli_runner(app, input_file)


@pytest.mark.parametrize(
    'input_file',
    [str(filepath.absolute())
     for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'new')).glob('*.txt'))],
    ids=[filepath.name.split('.')[0]
         for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'new')).glob('*.txt'))])
def test_new_peals(mock_bellboard_server, input_file: int):
    cli_runner(app, input_file)


@pytest.mark.parametrize(
    'input_file',
    [str(filepath.absolute())
     for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'search')).glob('*.txt'))],
    ids=[filepath.name.split('.')[0]
         for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'search')).glob('*.txt'))])
def test_peal_search(mock_bellboard_server, input_file: int):
    cli_runner(app, input_file)


@pytest.mark.parametrize(
    'input_file',
    [str(filepath.absolute())
     for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'report')).glob('*.txt'))],
    ids=[filepath.name.split('.')[0]
         for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'report')).glob('*.txt'))])
def test_report(mock_bellboard_server, input_file: int):
    cli_runner(app, input_file)


@pytest.mark.parametrize(
    'input_file',
    [str(filepath.absolute())
     for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'csv')).glob('*.txt'))],
    ids=[filepath.name.split('.')[0]
         for filepath in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), 'files', 'peals', 'csv')).glob('*.txt'))])
def test_csv_import(mock_bellboard_server, input_file: int):
    csv_file = os.path.join(os.path.dirname(input_file), os.path.basename(input_file).replace('.txt', '.csv'))
    assert os.path.exists(csv_file)
    tmp_file = os.path.join(os.path.dirname(csv_file), 'current.csv')
    shutil.copy(csv_file, tmp_file)
    try:
        cli_runner(app, input_file)
    finally:
        os.remove(tmp_file)
