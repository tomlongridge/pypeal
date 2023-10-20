import logging
from typing import Annotated
import typer

from rich import print

from pypeal.bellboard import get_peal as get_bellboard_peal, get_id_from_url, get_url_from_id
from pypeal.cli.prompts import ask_int, choose_option, ask, confirm, panel, error
from pypeal.db import initialize as initialize_db
from pypeal.method import Method, Stage
from pypeal.peal import Peal
from pypeal.ringer import Ringer
from pypeal.config import set_config_file

logger = logging.getLogger('pypeal')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

app = typer.Typer()


@app.command()
def main(
        action: Annotated[str, typer.Argument(help="Action to perform.")] = None,
        reset_database: Annotated[bool, typer.Option(help="Reset the database")] = False,
        clear_data: Annotated[bool, typer.Option(help="Clear peal data")] = False,
        peal_id_or_url: Annotated[str, typer.Option("--peal", help="The Bellboard peal ID or URL")] = None,
        config: Annotated[str, typer.Option(help="Path to config file.")] = None,
        ):

    if config:
        try:
            set_config_file(config)
        except FileNotFoundError as e:
            error(f'Unable to load file {config}: {e}')
            raise typer.Exit()

    initialize_or_exit(reset_database, clear_data)

    match action:
        case None:
            run_interactive(peal_id_or_url)
        case 'add':
            run_add(peal_id_or_url)
        case 'view':
            run_view(peal_id_or_url)
        case _:
            error(f'Unknown action: {action}')


def run_add(peal_id_or_url: str):
    _, url = prompt_peal_id(peal_id_or_url)
    add_peal(url)


def run_view(peal_id_or_url: str):
    peal_id, _ = prompt_peal_id(peal_id_or_url)
    panel(str(Peal.get(bellboard_id=peal_id)))
    confirm(None, 'Continue?')


def run_interactive(peal_id_or_url: str):

    while True:
        peals: dict[str, Peal] = Peal.get_all()
        panel(f'Number of peals: {len(peals)}')

        match choose_option(['Add peal by URL', 'Add random peal', 'View method', 'Update methods', 'Exit'], default=1):
            case 1:
                peal_id, bb_url = prompt_peal_id(peal_id_or_url)
                if peal_id in peals:
                    error(f'Peal {peal_id} already added')
                elif bb_url:
                    add_peal(bb_url)
            case 2:
                add_peal()
            case 3:
                run_view(peal_id_or_url)
            case 4:
                Method.update()
            case 5 | None:
                raise typer.Exit()

        peal_id_or_url = None


def add_peal(url: str = None) -> Peal:

    peal: Peal = get_bellboard_peal(url)

    prompt_add_methods(peal)
    prompt_add_ringers(peal)

    # Confirm commit
    panel(str(peal), title=get_url_from_id(peal.bellboard_id))
    if confirm('Save this peal?'):
        peal.commit()
        print(f'Peal {peal.bellboard_id} added')
        return peal
    else:
        return None


def prompt_add_method(method: Method = None) -> Method:

    original_title: str = method.title if method else None
    matched_method: Method = None
    exact_match: bool = True
    while matched_method is None:

        if method is not None:
            full_method_match = Method.search(name=method.name,
                                              exact_match=exact_match,
                                              classification=method.classification,
                                              stage=method.stage)
        else:
            full_method_match = []

        match len(full_method_match):
            case 0:
                if method:
                    print(f'No methods match "{method.title}"')
                match choose_option(['Search alternatives'], default=1, cancel_option='Cancel'):
                    case 1:
                        print('Enter search criteria:')
                        name = ask('Name', default=method.name if method else None)
                        stage = Stage(ask_int('Stage', default=method.stage.value if method else None, min=2, max=22))
                        classification_list = ['Bob', 'Place', 'Surprise', 'Treble Bob', 'Treble Place']
                        classification = choose_option(classification_list,
                                                       default=method.classification if method else None,
                                                       return_option=True,
                                                       cancel_option='None')
                        method = Method(None, name=name, classification=classification, stage=stage)
                        exact_match = False
                    case None:
                        return None
            case 1:
                matched_method = full_method_match[0]
            case _:
                print(f'{len(full_method_match)} methods match "{method.title}"')
                matched_method = choose_option(full_method_match, cancel_option='None', return_option=True)

    if ((original_title is not None and confirm(f'Matched "{original_title}" to method "{matched_method}" (ID: {matched_method.id})')) or
            (original_title is None and confirm(f'Add "{matched_method}" (ID: {matched_method.id})'))):
        return matched_method
    else:
        return None


def prompt_add_methods(peal: Peal):

    print(f'Matching peal titled "{peal.method_title}"...')

    # Attempt an easy match against a single method using the exact title
    if peal.title:
        full_method_match = Method.search(name=peal.title, exact_match=True, classification=peal.classification, stage=peal.stage)
        match len(full_method_match):
            case 0:
                # Continue to search
                pass
            case 1:
                if confirm(f'Matched "{peal.method_title}" to method "{full_method_match[0]}" (ID: {full_method_match[0].id})'):
                    peal.method = full_method_match[0]
                    peal.title = None
                    peal.is_mixed = False
                    peal.is_spliced = False
                    return
            case _:
                print(f'{len(full_method_match)} methods match "{peal.method_title}"')
                peal.method = choose_option(full_method_match, cancel_option='None', return_option=True)
                peal.title = None
                peal.is_mixed = False
                peal.is_spliced = False
                return

    # If it's not clear from the title, prompt for multi-method peal
    if peal.is_spliced is None or peal.is_mixed is None:
        peal.is_spliced = confirm(None, confirm_message='Is this a spliced peal?', default=False)
        peal.is_mixed = False
        if not peal.is_spliced:
            peal.is_mixed = confirm(None, confirm_message='Is this a mixed peal?', default=False)
            if not peal.is_mixed:
                if confirm(f'Other performance: {peal.method_title}', default=True):
                    peal.title = peal.method_title
                    peal.classification = None
                    peal.stage = None
                    peal.method = None
                    return

    # We haven't matched a method but it's not multi-method, start a single method search
    if peal.is_spliced is False and peal.is_mixed is False:

        while not peal.method:

            print(f'Attempting to match single method "{peal.title}"')

            match choose_option(['Search alternatives', 'Change to mixed methods', 'Change to spliced methods'],
                                default=1,
                                cancel_option='Cancel'):
                case 1:
                    name = ask('Name', default=peal.title if peal.title else None)
                    stage = Stage(ask_int('Stage', default=peal.stage.value, min=2, max=22))
                    classification = choose_option(['Bob', 'Place', 'Surprise', 'Treble Bob', 'Treble Place'],
                                                   default=peal.classification,
                                                   return_option=True)
                    potential_methods = Method.search(name=name, classification=classification, stage=stage)
                    print(f'{len(potential_methods)} methods match')
                    peal.method = choose_option(potential_methods, cancel_option='None', return_option=True)
                case 2:
                    peal.is_mixed = True
                    peal.is_spliced = False
                    prompt_add_methods(peal)
                    return
                case 3:
                    peal.is_spliced = True
                    peal.is_mixed = False
                    prompt_add_methods(peal)
                    return
                case None:
                    return

        peal.title = None
        return

    # Multi-method peal - remove title
    peal.title = None

    while True:

        while True:
            peal.num_methods = ask_int('Number of methods', default=peal.num_methods)
            peal.num_principles = ask_int('Number of principles', default=peal.num_principles)
            peal.num_variants = ask_int('Number of variants', default=peal.num_variants)
            if peal.num_methods + peal.num_principles + peal.num_variants > 0:
                break
        peal.stage = Stage(ask_int('Stage', default=peal.stage.value, min=2, max=22))
        peal.classification = choose_option(['Bob', 'Place', 'Surprise', 'Treble Bob', 'Treble Place', None],
                                            default=peal.classification,
                                            return_option=True)
        if peal.classification is None:
            peal.is_variable_cover = confirm(None, 'Is this peal variable cover?', default=False)

        if confirm(f'{peal.method_title}'):
            peal.title = None
            peal.method = None
            break

    print('Adding changes of methods to multi-method peal...')

    bb_methods = peal.methods
    peal.clear_methods()
    for method, changes in bb_methods:
        while not (new_method := prompt_add_method(method)):
            if confirm('No method matched', confirm_message=f'Remove "{method.title}"?'):
                break
        peal.add_method(new_method, changes)

    while confirm(None, confirm_message='Add more changes of method?' if len(bb_methods) else 'Add changes of method?', default=False):
        if method := prompt_add_method():
            peal.add_method(method, None)


def prompt_add_ringers(peal: Peal):

    # Track the bell, allowing for multiple bells per ringer
    bell: int = 1
    matched_ringers: list[tuple[Ringer, list[int], bool]] = [None]*len(peal.ringers)
    bb_ringer: tuple[Ringer, list[int], bool]
    for index, bb_ringer in enumerate(peal.ringers):

        # Holds the ringer record that matches the name found on Bellboard
        matched_ringer: Ringer = None

        full_name_match = Ringer.get_by_full_name(bb_ringer[0].name)
        match len(full_name_match):
            case 0:
                pass  # Allow to continue to name matching
            case 1:
                matched_ringer = prompt_add_ringer(bb_ringer[0].name, full_name_match[0], bb_ringer[1])
            case _:
                print(f'{bell}: {len(full_name_match)} existing ringers match "{bb_ringer[0].name}"')
                matched_ringer = choose_option(
                    [f'{r.name} ({r.id})' for r in full_name_match], values=full_name_match, cancel_option='None', return_option=True)

        while not matched_ringer:

            print(f'{bell}: No existing ringers match "{bb_ringer[0].name}"')

            match choose_option(['Add as new ringer', 'Search alternatives'], default=1, cancel_option='Cancel'):
                case 1:
                    if (ringer_names := prompt_ringer_names(bb_ringer[0].last_name, bb_ringer[0].given_names)):
                        matched_ringer = Ringer(*ringer_names)
                case 2:
                    if not (ringer_names := prompt_ringer_names(bb_ringer[0].last_name, bb_ringer[0].given_names)):
                        break
                    last_name, given_names = ringer_names
                    potential_ringers = Ringer.get_by_name(last_name, given_names)
                    match len(potential_ringers):
                        case 0:
                            print(f'No existing ringers match (given name: "{given_names}", last name: "{last_name}")')
                        case 1:
                            matched_ringer = prompt_add_ringer(bb_ringer[0].name, potential_ringers[0], bb_ringer[1])
                        case _:
                            print(f'{len(potential_ringers)} existing ringers match "{(given_names + " " + last_name).strip()}"')
                            matched_ringer = choose_option(potential_ringers, cancel_option='None', return_option=True)
                case None:
                    return None

        if matched_ringer.id is None:
            matched_ringer.commit()

        if len(full_name_match) == 0 and \
           f'{bb_ringer[0].given_names} {bb_ringer[0].last_name}' != matched_ringer.name and \
           confirm(f'Add "{bb_ringer[0].given_names} {bb_ringer[0].last_name}" as an alias?'):
            matched_ringer.add_alias(bb_ringer[0].last_name, bb_ringer[0].given_names)

        matched_ringers[index] = (matched_ringer, bb_ringer[1], bb_ringer[2])
        bell += len(bb_ringer[1])  # Keep track of how many bells are added for next prompt

    peal.clear_ringers()
    for ringer in matched_ringers:
        peal.add_ringer(*ringer)


def prompt_peal_id(peal_id: str = None) -> tuple[int, str]:

    while True:
        if peal_id is None:
            peal_id = ask('Bellboard URL or peal ID')
        if peal_id := validate_peal_input(peal_id):
            break
        else:
            error('Invalid Bellboard URL or peal ID')

    return (peal_id, get_url_from_id(peal_id))


def validate_peal_input(id_or_url: str) -> int:
    if id_or_url.isnumeric():
        return int(id_or_url)
    else:
        return get_id_from_url(id_or_url)


def prompt_add_ringer(name: str, ringer: Ringer, bells: list[int]) -> Ringer:
    if confirm(f'{",".join([str(bell) for bell in bells])}: "{name}" -> {ringer}',
               confirm_message='Is this the correct ringer?',
               default=True):
        return ringer
    return None


def prompt_ringer_names(default_last_name: str = None, default_given_names: str = None) -> tuple[str, str]:
    if (last_name := ask('Last name', default=default_last_name)) and \
       (given_names := ask('Given name(s)', default=default_given_names)):
        return last_name, given_names
    return None


def initialize_or_exit(reset_db: bool, clear_data: bool):
    if not initialize_db(reset_db):
        error('Unable to connect to pypeal database')
        raise typer.Exit()
    if reset_db:
        Method.update()
    if clear_data:
        Peal.clear_data()
        Ringer.clear_data()
