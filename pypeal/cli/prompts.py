from rich.prompt import IntPrompt
from rich import print


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
        return None
    elif return_option:
        return options[choice - 1]
    else:
        return choice
