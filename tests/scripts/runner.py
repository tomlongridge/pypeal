import re
from typer import Typer
from typer.testing import CliRunner
from click.testing import Result

from pypeal.peal import Peal


_runner = CliRunner()


def cli_runner(app: Typer, input_file: str):

    with open(input_file, 'r') as f:
        test_data = [data.strip() for data in f.read().split('===')]

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
    stored_peal: Peal = None
    test_output = ''
    try:
        result = _runner.invoke(app,
                                test_data[0].split('|') if test_data[0] != '' else None,
                                input='\n'.join(stdin) + '\n')

        last_peal_id = None
        for line in result.output.split('\n'):
            if line.startswith('[User input:') and len(stdin) > 0:
                test_output += '>>> ' + stdin.pop(0) + '\n'
            if peal_id_match := re.match(r'Peal \(ID (\d+)\) added', line):
                last_peal_id = int(peal_id_match.group(1))
            test_output += line + '\n'
        for remaining_input in stdin:
            test_output += '>>> ' + remaining_input + '\n'

        if result.exception and type(result.exception) is not SystemExit:
            raise result.exception

        assert result.exit_code == 0, "App exited with non-zero exit code"

        assert last_peal_id is not None, "Unable to find saved peal ID"
        stored_peal = Peal.get(id=last_peal_id)
        assert stored_peal is not None, "Unable to retrieve saved peal"
        assert str(stored_peal) == test_data[2], "Saved peal does not match expected peal"

        assert result.output.strip() == expected_stdout, "App output does not match expected output"

    except Exception as e:
        with open(input_file, 'w') as f:
            f.write(test_data[0] +
                    '\n===\n' +
                    test_output.strip() +
                    '\n===\n' +
                    str(stored_peal))
        raise e
