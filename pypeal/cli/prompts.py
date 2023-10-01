import logging
from rich.prompt import IntPrompt, Prompt, Confirm
from rich import print

from pypeal.config import get_config

logger = logging.getLogger('pypeal')


def print_user_input(prompt: str, message: str):
    logger.debug(f'User input >> {prompt}: {message}')
    if get_config('diagnostics', 'print_user_input') == 'True':
        print(f'User input >> {message}')


def ask(prompt: str, default: str = None) -> str:
    response = Prompt.ask(prompt, default=default)
    print_user_input(prompt, response)
    return response


def confirm(prompt: str, confirm_message: str = 'Is this correct?', default: bool = None) -> bool:
    print(prompt)
    response = Confirm.ask(confirm_message, default=None if default is None else 'y' if default else 'n')
    print_user_input(confirm_message, response)
    return response


def option_prompt(options: list[any],
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
    choice = IntPrompt.ask('Select action',
                           choices=[str(v) for v in range(1, len(option_list)+1)],
                           default=default,
                           show_choices=False,
                           show_default=True)

    if cancel_option and choice == len(option_list):
        response = None
    elif return_option:
        response = options[choice - 1]
    else:
        response = choice
    print_user_input(prompt_text, response)

    return response
