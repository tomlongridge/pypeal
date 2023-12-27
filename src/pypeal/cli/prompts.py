from datetime import datetime, timedelta
import logging
from rich.prompt import IntPrompt, Prompt, Confirm
from rich.panel import Panel
from rich import print
from rich.style import Style
from rich.padding import Padding
from rich.markup import escape
from pypeal import utils

from pypeal.config import get_config

logger = logging.getLogger('pypeal')

_heading_style = Style(color="white", bgcolor="cyan", bold=True)


class UserCancelled(Exception):
    pass


def print_user_input(prompt: str, message: str):
    logger.debug(f'User input >> {prompt}: {message}')
    if get_config('diagnostics', 'print_user_input'):
        if message == datetime.now().strftime('%Y/%m/%d'):  # Avoid printing today's date so it doesn't change in test
            message = '[Today]'
        print(f'\n[User input: "{message}"]')


def ask(prompt: str, default: str = None, required: bool = True) -> str:
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
                if not required or default is None:
                    break
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
            response = ask(prompt,
                           default=default.strftime('%Y/%m/%d') if default else None,
                           required=required)
            if default is None and response is None:
                break
            if response is not None:
                if response.isnumeric() or (response.startswith('-') and response[1:].isnumeric()):
                    response = (default or datetime.date(datetime.now())) + timedelta(days=int(response))
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


def prompt_names(default_last_name: str = None, default_given_names: str = None) -> tuple[str, str]:
    last_name = ask('Last name', default=default_last_name, required=True)
    given_names = ask('Given name(s)', default=default_given_names, required=False)
    return last_name, given_names


def panel(content: str, title: str = 'pypeal'):
    print(Panel(escape(content), title=title))


def warning(message: str, title: str = None):
    print(Panel(f'[bold yellow]Warning:[/] {message}', title=title))


def error(message: str, title: str = None):
    print(Panel(f'[bold red]Error:[/] {message}', title=title))


def heading(message: str):
    print()
    print(Padding(message, (1, 1), style=_heading_style))
    print()
