from typer.testing import CliRunner

from pypeal.peal import Peal
from pypeal.cli.app import app


runner = CliRunner()


def test_app():
    result = runner.invoke(app,
                           ['--reset-database'],
                           input='1\n22152\n\n\n\n\n\n\n\n\n3\n',
                           env={'PYPEAL_CONFIG': 'tests/files/test_config.ini'})
    assert result.exit_code == 0
    stored_peal = Peal.get(bellboard_id=22152)
    assert stored_peal is not None
