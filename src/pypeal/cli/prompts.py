from datetime import datetime, timedelta
import logging
from rich.prompt import IntPrompt, Prompt, Confirm
from rich.panel import Panel
from rich import print
from rich.markup import escape

from pypeal.config import get_config

logger = logging.getLogger('pypeal')


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
            response = Prompt.ask(prompt, default=default, show_default=(default is not None))
            if not required or response:
                print_user_input(prompt, response)
                return response
    except KeyboardInterrupt:
        print_user_input(prompt, '[Abort]')
        print()  # Ensure subsequent prompt is on a new line
        raise UserCancelled()


def ask_int(prompt: str, default: int = None, min: int = None, max: int = None) -> int:
    try:
        while True:
            response = IntPrompt.ask(prompt, default=default, show_default=(default is not None))
            if default is None and response is None:
                break
            if response is not None:
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
                else:
                    try:
                        response = datetime.date(datetime.strptime(response, '%Y/%m/%d'))
                    except ValueError:
                        try:
                            response = datetime.date(datetime.strptime(response, '%Y-%m-%d'))
                        except ValueError:
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


def choose_option(options: list[any],
                  values: list[any] = None,
                  prompt: str = 'Options',
                  default: any = None,
                  return_option: bool = False,
                  cancel_option: str = None,
                  required: bool = True) -> any:
    prompt_text = f'{prompt}: '
    option_list = [*options] + ([cancel_option] if cancel_option else [])
    for i, option in enumerate(option_list):
        prompt_text += '\n' if len(option_list) > 5 else ''
        prompt_text += f'{i + 1}) {option}'
        prompt_text += ', ' if len(option_list) <= 5 and i < len(option_list) - 1 else ''
    choice = None
    if type(default) is int:
        default_value = default
    elif default in options:
        default_value = option_list.index(default) + 1
    else:
        default_value = None
    while not choice:
        print(prompt_text)
        try:
            choice = IntPrompt.ask('Select action',
                                   choices=[str(v) for v in range(1, len(option_list)+1)],
                                   default=default_value,
                                   show_choices=False,
                                   show_default=True)
        except KeyboardInterrupt:
            print_user_input(prompt_text, '[Abort]')
            print()  # Ensure subsequent prompt is on a new line
            raise UserCancelled()

        if choice is None:
            if required:
                error('Please choose an option')
                continue
            else:
                response = None
                print_user_input(prompt_text, 'None')
        elif cancel_option and choice == len(option_list):
            response = None
            print_user_input(prompt_text, cancel_option)
        elif return_option:
            response = values[choice - 1] if values else options[choice - 1]
            print_user_input(prompt_text, f'{response} ({choice})')
        else:
            response = choice
            print_user_input(prompt_text, f'{choice}')

    return response


def prompt_names(default_last_name: str = None, default_given_names: str = None) -> tuple[str, str]:
    last_name = ask('Last name', default=default_last_name, required=True)
    given_names = ask('Given name(s)', default=default_given_names, required=False)
    return last_name, given_names


def panel(content: str, title: str = 'pypeal'):
    print(Panel(escape(content), title=title))


def warning(message: str):
    print(Panel(f'[bold yellow]Warning:[/] {message}'))


def error(message: str):
    print(Panel(f'[bold red]Error:[/] {message}'))
