from typer.testing import CliRunner

import sys
sys.path.append('../pypeal')
from pypeal.cli.app import app  # noqa: E402


runner = CliRunner()


def test_app():
    result = runner.invoke(app, ['--reset-database'], input='1\n22152\n\n\n\n\n\n\n\n\n3\n', env={'PYPEAL_CONFIG': 'tests/files/test_config.ini'})
    assert result.exit_code == 0
