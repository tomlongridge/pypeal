import datetime
import logging
from rich.prompt import IntPrompt, Prompt, Confirm
from rich.panel import Panel
from rich import print
from rich.style import Style
from rich.padding import Padding
from rich.text import Text
from rich.markup import escape
from pypeal import utils

from pypeal.bellboard.utils import get_url_from_id
from pypeal.config import get_config
from pypeal.entities.peal import Peal

logger = logging.getLogger('pypeal')

_heading_style = Style(color="white", bgcolor="cyan", bold=True)


class UserCancelled(Exception):
    pass


def print_user_input(prompt: str, message: str):
    logger.debug(f'User input >> {prompt}: {message}')
    if get_config('diagnostics', 'print_user_input'):
        print(f'\n[User input: "{message}"]')


def format_timestamp(date: any):
    if get_config('diagnostics', 'print_user_input'):
        return '[Timestamp]'
    else:
        return date.strftime("%d-%b-%Y %H:%M:%S")


def ask(prompt: str, default: any = None, required: bool = True) -> str:
    try:
        while True:
            response = Prompt.ask(prompt, default=str(default) if default else None, show_default=default is not None)
            if response is not None and response.strip() == '':  # Allow empty string to indicate no value when there's a default value
                response = None
            if not required or response:
                print_user_input(prompt, response)
                return response
    except KeyboardInterrupt:
        print_user_input(prompt, '[Abort]')
        print()  # Ensure subsequent prompt is on a new line
        raise UserCancelled()


def ask_int(prompt: str, default: int = None, min: int = None, max: int = None, required: bool = True) -> int:
    try:
        while True:
            response = IntPrompt.ask(prompt, default=default, show_default=(default is not None))
            if response is None:
                if not required:
                    break
                else:
                    continue
            else:
                if min is not None and response < min:
                    error(f'Number must be {min} or more')
                    continue
                if max is not None and response > max:
                    error(f'Number must be {max} or less')
                    continue
            break
    except KeyboardInterrupt:
        print_user_input(prompt, '[Abort]')
        print()  # Ensure subsequent prompt is on a new line
        raise UserCancelled()
    print_user_input(prompt, response)
    return response


def ask_date(prompt: str,
             default: datetime.date = None,
             min: datetime.date = None,
             max: datetime.date = None,
             required: bool = True) -> datetime.date:
    try:
        while True:
            response = ask(f'{prompt} (yyyy/mm/dd)',
                           default=default.strftime('%Y/%m/%d') if default else None,
                           required=required)
            if default is None and response is None:
                break
            if response is not None:
                if response.isnumeric() or (response.startswith('-') and response[1:].isnumeric()):
                    response = (default or utils.get_now().date()) + datetime.timedelta(days=int(response))
                elif not (response := utils.parse_date(response)):
                    error('Invalid date - please enter in format yyyy/mm/dd')
                    continue
                if min is not None and response < min:
                    error(f'Date must be on or after {min.strftime("%Y/%m/%d")}')
                    continue
                if max is not None and response > max:
                    error(f'Date must be on or before {max.strftime("%Y/%m/%d")}')
                    continue
            break
    except KeyboardInterrupt:
        print_user_input(prompt, '[Abort]')
        print()  # Ensure subsequent prompt is on a new line
        raise UserCancelled()
    return response


def confirm(prompt: str, confirm_message: str = 'Is this correct?', default: bool = True) -> bool:
    try:
        if prompt:
            print(prompt)
        response = Confirm.ask(confirm_message, default=default, show_default=True)
        print_user_input(confirm_message, response)
        return response
    except KeyboardInterrupt:
        print_user_input(prompt, '[Abort]')
        print()  # Ensure subsequent prompt is on a new line
        raise UserCancelled()


def press_any_key(prompt: str = 'Press any key to continue...'):
    try:
        input(prompt)
        print_user_input(prompt, '[Continue]')
    except KeyboardInterrupt:
        print_user_input(prompt, '[Abort]')
        print()  # Ensure subsequent prompt is on a new line
        raise UserCancelled()


def make_peal_panel(peal: str | Peal, title: str = None):
    if type(peal) is str:
        return Panel(escape(peal), title=title, width=80)
    else:
        if peal.bellboard_id and not title:
            title = get_url_from_id(peal.bellboard_id)
        return Panel(escape(str(peal)), title=title, width=80)


def panel(content: str | Peal, title: str = None, width: int = None):
    if type(content) is Peal:
        print(make_peal_panel(content, title))
    else:
        print(Panel(escape(content), title=title, width=width))


def warning(message: str, title: str = None):
    print(Panel(f'[bold yellow]Warning:[/] {message}', title=title))


def error(message: str, title: str = None):
    print(Panel(f'[bold red]Error:[/] {message}', title=title))


def heading(message: str, full: bool = False):
    if get_config('diagnostics', 'print_user_input'):
        print(message)
    else:
        if full:
            print(Padding(Text(f'\n{message}\n', style=_heading_style, justify='center'), (1, 1)))
        else:
            print(Padding(Text(f' > {message}', style=_heading_style, justify='left'), (1, 0, 0, 0)))


# Iterates through dict and uses key names to prompt for values, with pre-existing values as defaults
def prompt_any(data: dict | list | str | int | bool, prompt: str) -> dict | list | str | int | bool:

    if data is None:
        return
    elif type(data) is bool:
        return confirm(None, prompt, default=data)
    elif type(data) is datetime.date:
        return ask_date(prompt, default=data)
    elif type(data) is str:
        return ask(prompt, default=data)
    elif type(data) is int:
        return ask_int(prompt, default=data)
    elif type(data) is list:
        return [prompt_any(value, f'{prompt} {i}') for i, value in enumerate(data, start=1)]
    elif type(data) is dict:
        if prompt is not None:
            print(prompt)
        nested_data = {}
        for field, value in data.items():
            if type(field) is not str:
                raise ValueError(f'Key names must be strings: "{field}" is {type(field)}')
            nested_data[field] = prompt_any(value, field.replace("_", " ").title())
        return nested_data
    else:
        raise ValueError(f'Unknown type for field "{data}": {type(data)}')
