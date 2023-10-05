import logging
from typing import Annotated
import typer

from rich import print

from pypeal.bellboard import get_peal as get_bellboard_peal, get_id_from_url, get_url_from_id
from pypeal.cli.prompts import choose_option, ask, confirm, panel, error
from pypeal.db import initialize as initialize_db
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
        reset_database: Annotated[bool, typer.Option(help="Reset the database first.")] = False,
        peal_id_or_url: Annotated[str, typer.Option("--peal", help="The Bellboard peal ID or URL")] = None,
        config: Annotated[str, typer.Option(help="Path to config file.")] = None,
        ):

    if config:
        try:
            set_config_file(config)
        except FileNotFoundError as e:
            error(f'Unable to load file {config}: {e}')
            raise typer.Exit()

    initialize_or_exit(reset_database)

    peal_id = None
    if peal_id_or_url:
        if (peal_id := validate_peal_input(peal_id_or_url)):
            logger.debug(f'Adding peal ID {peal_id} provided as "add-peal" option')
        else:
            error(f'Invalid Bellboard URL or peal ID: {peal_id_or_url}')
            raise typer.Exit()

    match action:
        case None | 'add':
            run_interactive(peal_id)
        case 'view':
            run_view(peal_id)
        case _:
            error(f'Unknown action: {action}')


def run_view(peal_id: int):
    if peal_id is None:
        error('No peal ID provided')
        raise typer.Exit()
    panel(str(Peal.get(bellboard_id=peal_id)))


def run_interactive(peal_id: int = None):

    while True:
        peals: dict[str, Peal] = Peal.get_all()
        panel(f'Number of peals: {len(peals)}')

        match choose_option(['Add peal by URL', 'Add random peal', 'Exit'], default=1) if peal_id is None else 1:
            case 1:
                bb_url = None
                while peal_id is None:
                    if not (peal_id := validate_peal_input(ask('Bellboard URL or peal ID'))):
                        error('Invalid Bellboard URL or peal ID')

                bb_url = get_url_from_id(peal_id)
                if peal_id in peals:
                    error(f'Peal {peal_id} already added')
                elif bb_url:
                    add_peal(bb_url)
            case 2:
                add_peal()
            case 3 | None:
                raise typer.Exit()

        peal_id = None


def add_peal(url: str = None) -> Peal:

    peal: Peal = get_bellboard_peal(url)

    # Attempt to match names to ringers

    bell: int = 1                                      # Track the bell, allowing for multiple bells per ringer
    bb_ringer: tuple[Ringer, int, bool]
    for index, bb_ringer in enumerate(peal.ringers):

        matched_ringer: Ringer = None                  # Holds the ringer record that matches the name found on Bellboard

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
            matched_ringer = Ringer.add(matched_ringer.last_name, matched_ringer.given_names)

        if len(full_name_match) == 0 and \
           f'{bb_ringer[0].given_names} {bb_ringer[0].last_name}' != matched_ringer.name and \
           confirm(f'Add "{bb_ringer[0].given_names} {bb_ringer[0].last_name}" as an alias?'):
            matched_ringer.add_alias(bb_ringer[0].last_name, bb_ringer[0].given_names)

        peal.ringers[index] = (matched_ringer, bb_ringer[1], bb_ringer[2])
        bell += len(bb_ringer[1])  # Keep track of how many bells are added for next prompt

    # Confirm commit
    panel(str(peal), title=get_url_from_id(peal.bellboard_id))
    if confirm('Save this peal?'):
        peal.commit()
        print(f'Peal {peal.bellboard_id} added')
        return peal
    else:
        return None


def validate_peal_input(id_or_url: str) -> int:
    if id_or_url.isnumeric():
        return int(id_or_url)
    else:
        return get_id_from_url(id_or_url)


def prompt_add_ringer(name: str, ringer: Ringer, bell: int) -> Ringer:
    if confirm(f'{bell}: "{name}" -> {ringer}', confirm_message='Is this the correct ringer?', default=True):
        return ringer
    return None


def prompt_ringer_names(default_last_name: str = None, default_given_names: str = None) -> tuple[str, str]:
    if (last_name := ask('Last name', default=default_last_name)) and \
       (given_names := ask('Given name(s)', default=default_given_names)):
        return last_name, given_names
    return None


def initialize_or_exit(reset_db: bool = False):
    if not initialize_db(reset_db):
        error('Unable to connect to pypeal database')
        raise typer.Exit()
