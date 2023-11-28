from pypeal.cli.prompts import ask, error

from pypeal.parsers import parse_duration
from pypeal.peal import Peal


def prompt_add_duration(duration_str: str, peal: Peal, quick_mode: bool):

    default_duration: int = None
    if duration_str is not None:
        try:
            default_duration = parse_duration(duration_str)
        except ValueError:
            default_duration = None
            error(f'Invalid duration: {duration_str}')

    if quick_mode:
        peal.duration = default_duration
        return

    while True:
        duration_str = ask('Duration', default=default_duration, required=False)
        if duration_str is None:
            break
        elif (duration := parse_duration(duration_str)) is not None:
            peal.duration = duration
            break
        else:
            error('Invalid duration')
