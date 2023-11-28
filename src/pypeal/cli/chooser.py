from pypeal.cli.prompts import UserCancelled, error, print_user_input
from rich.prompt import Prompt
from rich.console import Console
from rich.table import Table

CHOOSE_INLINE_THRESHOLD = 5
CHOOSE_OPTIONS_PER_PAGE = 45
CHOOSE_OPTIONS_PER_COLUMN = 15
CHOOSE_NONE_OPTION_CHAR = 'x'


def choose_option(options: list[any],
                  values: list[any] = None,
                  title: str = None,
                  prompt: str = 'Select option',
                  default: any = None,
                  none_option: str = None) -> any:

    page_num = 1
    options_by_page: list[list[any]] = []
    if len(options) > CHOOSE_INLINE_THRESHOLD:
        for i in range(0, len(options)):
            if i // CHOOSE_OPTIONS_PER_PAGE >= len(options_by_page):
                options_by_page.append([])
            options_by_page[i // CHOOSE_OPTIONS_PER_PAGE].append(options[i])

    if default and type(default) is not int:
        if values and default in values:
            default = values.index(default) + 1
        elif default in options:
            default = options.index(default) + 1

    while True:

        action_list = []
        if len(options) <= CHOOSE_INLINE_THRESHOLD:
            if none_option:
                prompt += f' (x = {none_option})'
            _print_options_inline(title, options)
        else:
            if page_num > 1:
                action_list.append('p) Previous page')
            elif page_num < len(options_by_page):
                action_list.append('n) Next page')
            if none_option:
                action_list.append(f'{CHOOSE_NONE_OPTION_CHAR}) {none_option}')
            _print_options_page(title, options_by_page[page_num - 1], action_list)

        try:
            choice = Prompt.ask(f'{prompt}', default=str(default) if default else None, show_default=True)
        except KeyboardInterrupt:
            print_user_input(prompt, '[Abort]')
            print()  # Ensure subsequent prompt is on a new line
            raise UserCancelled()

        if choice is None and none_option is None:
            error('Please choose an option')  # If there is no default and nothing is entered
        elif choice is None or choice == CHOOSE_NONE_OPTION_CHAR:
            print_user_input(prompt, 'None')
            return None  # choice is None if it's the default
        elif not choice.isnumeric():
            if choice == 'p' and page_num > 1:
                page_num -= 1
            elif choice == 'n' and page_num < len(options_by_page):
                page_num += 1
            else:
                error('Input an option number or one of the following:\n\n' + '\n  - '.join(action_list))
        else:
            choice = int(choice)
            if choice > 0 and choice <= len(options):
                if values:
                    response = values[((page_num - 1) * CHOOSE_OPTIONS_PER_PAGE) + choice - 1]
                elif type(options[0]) is not str:
                    response = options[((page_num - 1) * CHOOSE_OPTIONS_PER_PAGE) + choice - 1]
                else:
                    response = choice
                print_user_input(prompt, response)
                return response
            else:
                error(f'The number must be between 1 and {len(options)}')


def _print_options_inline(title: str, options: list[any]):
    options_str = f'{title}: ' if title else ''
    for i, option in enumerate(options):
        options_str += f'{i + 1}) {option}'
        options_str += ', ' if i < len(options) - 1 else ''
    print(options_str)


def _print_options_page(title: str, options: list[any], actions: list[str]):
    if title:
        print(f'{title}:')
    table = Table(show_header=False, show_footer=False, expand=True)
    for i in range(CHOOSE_OPTIONS_PER_COLUMN):
        row = []
        for j in range((len(options) // CHOOSE_OPTIONS_PER_COLUMN) + 1):
            index = i + (j*CHOOSE_OPTIONS_PER_COLUMN)
            if index < len(options):
                row.append(f'{index + 1}) {options[index]}')
            else:
                break
        if len(row) > 0:
            table.add_row(*row)
        else:
            break
    if actions:
        table.add_section()
        for action in actions:
            table.add_row(action)
    console = Console()
    console.print(table)


# print(prompt_choose('This?', ['a', 'b', 'c'], [1, 2, 3], none_option='None'))

# print(prompt_choose('This?', ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k']))
