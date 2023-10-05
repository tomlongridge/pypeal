import os
import pytest
from xprocess import ProcessStarter, XProcess


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
