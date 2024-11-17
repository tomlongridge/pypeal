from itertools import zip_longest
import os
import re
from typer import Typer
from typer.testing import CliRunner
from click.testing import Result

from pypeal.entities.peal import Peal


NO_PEAL_MARKER = 'No peal'


_runner = CliRunner()


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


def cli_runner(app: Typer, input_file: str):

    with open(input_file, 'r') as f:
        test_data = [data.strip() for data in f.read().split('===')]

    assert len(test_data) == 4, f'Test file for peal {input_file} doesn\'t contain the expected 4 sections'

    args, search_responses, console_text, expected_peal = test_data[:4]

    if expected_peal == NO_PEAL_MARKER:
        expected_peal = None

    stdin: list[str] = []
    comments: list[str] = []
    expected_stdout = ''
    for stdout_line in console_text.split('\n'):
        comments.append(stdout_line if stdout_line.startswith('###') else None)
        if stdout_line.startswith('>>> '):
            stdin.append(stdout_line[4:])
        elif stdout_line.startswith('!!!') or stdout_line.startswith('###'):  # Don't expect errors or comments
            pass
        else:
            expected_stdout += stdout_line + '\n'
    expected_stdout = expected_stdout.strip()

    if search_responses:
        set_search_results([int(peal_id) for peal_id in search_responses.split('|') if peal_id != ''])
    else:
        set_search_results(None)

    result: Result = None
    stored_peal: Peal = None
    test_output = ''
    try:
        result = _runner.invoke(app,
                                args.split('|') if args != '' else None,
                                input='\n'.join(stdin) + '\n')

        last_peal_id = None
        for stdout_line, comment_line in zip_longest(result.output.split('\n'), comments):
            if comment_line is not None:
                test_output += comment_line + '\n'
            if stdout_line is not None:
                if stdout_line.startswith('[User input:') and len(stdin) > 0:
                    test_output += '>>> ' + stdin.pop(0) + '\n'
                if peal_id_match := re.match(r'Peal \(ID (\d+)\) added', stdout_line):
                    last_peal_id = int(peal_id_match.group(1))
                test_output += stdout_line + '\n'
        for remaining_input in stdin:
            test_output += '>>> ' + remaining_input + '\n'

        if result.exception and type(result.exception) is not SystemExit:
            raise result.exception

        assert result.exit_code == 0, "App exited with non-zero exit code"

        if last_peal_id:
            stored_peal = Peal.get(id=last_peal_id)
        else:
            stored_peal = None

        if expected_peal is not None:
            assert last_peal_id is not None, "Unable to find saved peal ID"
            assert stored_peal is not None, "Unable to retrieve saved peal"
            assert str(stored_peal) == expected_peal, "Saved peal does not match expected peal"

        assert result.output.strip() == expected_stdout, "App output does not match expected output"

        _update_input_file(input_file, args, search_responses, test_output, stored_peal)

    except Exception as e:
        _update_input_file(input_file, args, search_responses, test_output, stored_peal, e)
        raise e


def _update_input_file(input_file: str,
                       args: str,
                       search_responses: str,
                       console_text: str,
                       stored_peal: Peal,
                       exception: Exception = None):
    output_text = ''
    for line in console_text.split('\n'):
        if not line.startswith('!!!'):
            output_text += line + '\n'
    with open(input_file, 'w') as f:
        f.write(args +
                '\n===\n' +
                search_responses + ('\n' if search_responses else '') +
                '===\n' +
                (f'!!! LAST RUN ENDED WITH AN ERROR:\n!!!\n!!! {exception}\n!!!\n\n' if exception else '') +
                output_text.strip() +
                '\n===\n' +
                (str(stored_peal) if stored_peal else NO_PEAL_MARKER))
