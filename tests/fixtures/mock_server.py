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
    set_search_results(None)


def set_search_results(bb_peal_ids: list[int]):
    response_file = os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'searches', 'test.xml')
    if bb_peal_ids is None:
        if os.path.exists(response_file):
            os.remove(response_file)
    else:
        with open(response_file, 'w') as f:
            f.write('<performances xmlns="http://bb.ringingworld.co.uk/NS/performances#">\n')
            for peal_id in bb_peal_ids:
                f.write(f'  <performance href="view.php?id={peal_id}"/>\n')
            f.write('</performances>')
