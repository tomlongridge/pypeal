import logging
from rich.prompt import IntPrompt, Prompt, Confirm
from rich.panel import Panel
from rich import print
from rich.markup import escape

from pypeal.config import get_config

logger = logging.getLogger('pypeal')


def print_user_input(prompt: str, message: str):
    logger.debug(f'User input >> {prompt}: {message}')
    if get_config('diagnostics', 'print_user_input') == 'True':
        print(f'User input >> {message}')


def ask(prompt: str, default: str = None) -> str:
    try:
        response = Prompt.ask(prompt, default=default)
        print_user_input(prompt, response)
        return response
    except KeyboardInterrupt:
        print_user_input(prompt, '[Abort]')
        print()  # Ensure subsequent prompt is on a new line
        return None


def confirm(prompt: str, confirm_message: str = 'Is this correct?', default: bool = True) -> bool:
    try:
        print(prompt)
        response = Confirm.ask(confirm_message, default='y' if default else 'n')
        print_user_input(confirm_message, response)
        return response
    except KeyboardInterrupt:
        print_user_input(prompt, '[Abort]')
        print()  # Ensure subsequent prompt is on a new line
        return None


def choose_option(options: list[any],
                  values: list[any] = None,
                  prompt: str = 'Options',
                  default: int = None,
                  return_option: bool = False,
                  cancel_option: str = None) -> any:
    prompt_text = f'{prompt}: '
    option_list = [*options] + ([cancel_option] if cancel_option else [])
    for i, option in enumerate(option_list):
        prompt_text += f'{i + 1}) {option}'
        prompt_text += ', ' if i < len(option_list) - 1 else ''
    print(prompt_text)
    try:
        choice = IntPrompt.ask('Select action',
                               choices=[str(v) for v in range(1, len(option_list)+1)],
                               default=default,
                               show_choices=False,
                               show_default=True)
    except KeyboardInterrupt:
        print_user_input(prompt_text, '[Abort]')
        print()  # Ensure subsequent prompt is on a new line
        return None

    if cancel_option and choice == len(option_list):
        response = None
        print_user_input(prompt_text, cancel_option)
    elif return_option:
        response = values[choice - 1] if values else options[choice - 1]
        print_user_input(prompt_text, f'{response} ({choice})')
    else:
        response = choice
        print_user_input(prompt_text, f'{choice}')

    return response


def panel(content: str, title: str = 'pypeal'):
    if get_config('diagnostics', 'print_user_input') != 'True':
        print(Panel(escape(content), title=title))
    else:
        print(escape(f'[{title} panel displayed]'))


def error(message: str):
    print(Panel(f'[bold red]Error:[/] {message}'))
