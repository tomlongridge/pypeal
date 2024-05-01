import os
from typing import Iterator
from pypeal.bellboard.utils import get_id_from_url
from pypeal.cli.chooser import choose_option
from pypeal.cli.prompts import ask, error
from pypeal.entities.peal import Peal


# Returns, or prompts for, a Bellboard ID or list of IDs or path to read
def prompt_peal_input(default_input: str = None, required: bool = True, allow_file: bool = False) -> Iterator[int | list[int] | str | None]:

    input = default_input or ask('Bellboard URL or peal ID' + (' (enter to exit)' if not required else ''), required=required)

    while True:
        if input is None:
            return None
        if ',' in input:
            for input_parts in input.split(','):
                yield from prompt_peal_input(input_parts.strip())
        elif input.isnumeric():
            yield int(input)
        elif input.startswith('http'):
            yield get_id_from_url(input)
        elif allow_file and os.path.exists(input):
            yield input
        else:
            error('Invalid Bellboard URL or peal ID')

        if default_input is not None:
            # If an input was provided, exit after one iteration
            break
        else:
            input = ask('Bellboard URL or peal ID (enter to exit)', required=False)


def prompt_peal_by_id(peal_id_or_url: str, ask_for_database_id: bool = False) -> Iterator[Peal]:
    is_bellboard_id = False
    if peal_id_or_url is None:
        if ask_for_database_id:
            is_bellboard_id = choose_option(['Bellboard ID/URL', 'Peal ID'], default=1) == 1
        else:
            is_bellboard_id = True
    for input in prompt_peal_input(peal_id_or_url):
        if is_bellboard_id:
            peal = Peal.get(bellboard_id=input)
            if not peal and not ask_for_database_id:
                peal = Peal.get(id=input)
        else:
            peal = Peal.get(id=input)

        if not peal:
            error('Peal not found')
        else:
            yield peal
