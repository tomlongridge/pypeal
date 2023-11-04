import logging
from typing import Annotated
import typer

from rich import print

from pypeal.bellboard.interface import BellboardError, get_id_from_url, get_url_from_id
from pypeal.bellboard.html_generator import HTMLPealGenerator
from pypeal.bellboard.xml_generator import XMLPealGenerator
from pypeal.cccbr import update_methods
from pypeal.cli.peal_prompter import PealPrompter
from pypeal.cli.prompts import UserCancelled, choose_option, ask, confirm, panel, error
from pypeal.db import initialize as initialize_db
from pypeal.dove import update_associations, update_bells, update_towers
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


__peals: dict[str, Peal] = None


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
    add_peal(prompt_peal_id(peal_id_or_url))


def run_view(peal_id_or_url: str):
    peal_id = prompt_peal_id(peal_id_or_url)
    panel(str(Peal.get(bellboard_id=peal_id)))
    confirm(None, 'Continue?')


def run_interactive(peal_id_or_url: str):

    while True:
        try:
            panel(f'Number of peals: {len(get_peal_list())}')

            match choose_option(['Add peal by URL',
                                 'Add random peal',
                                 'Add peal by search',
                                 'View peal',
                                 'Update method data',
                                 'Update Dove data',
                                 'Exit'],
                                default=1):
                case 1:
                    add_peal(prompt_peal_id(peal_id_or_url))
                case 2:
                    add_peal()
                case 3:
                    search_peals()
                case 4:
                    run_view(peal_id_or_url)
                case 5:
                    update_methods()
                case 6:
                    update_associations()
                    update_towers()
                    update_bells()
                case 7 | None:
                    raise typer.Exit()
        except UserCancelled:
            continue

        peal_id_or_url = None


def add_peal(peal_id: int = None):

    if peal_id in get_peal_list():
        error(f'Peal {peal_id} already added to database')
        return

    generator = HTMLPealGenerator(PealPrompter())

    try:
        peal = generator.get(peal_id)
    except BellboardError as e:
        logger.exception('Error getting peal from Bellboard: %s', e)
        error(e)
        return

    panel(str(peal), title=get_url_from_id(peal.bellboard_id))
    if confirm('Save this peal?'):
        peal.commit()
        print(f'Peal {peal.bellboard_id} added')


def search_peals():

    name: str = ask('Ringer name')

    listener = PealPrompter()
    generator = XMLPealGenerator(listener)
    peal_gen = generator.search(name)

    # Loop through using the generator, which yields the peal ID to check if it exists
    # we then send back a true/false to the generator to tell it whether to continue
    finished_search_results = None
    peal_id = next(peal_gen)
    while finished_search_results is not True:

        # Allow user to exit after first peal
        if finished_search_results is not None and not confirm(None, 'Add next peal?', default=True):
            break

        peal_exists = peal_id in get_peal_list()
        finished_search_results = False
        try:
            peal_id = peal_gen.send(not peal_exists)
        except StopIteration:
            finished_search_results = True
        peal = listener.peal
        panel(str(peal), title=get_url_from_id(peal.bellboard_id))
        if confirm('Save this peal?'):
            peal.commit()
            print(f'Peal {peal.bellboard_id} added')


def prompt_peal_id(peal_id: str = None) -> int:

    while True:
        if peal_id is None:
            peal_id = ask('Bellboard URL or peal ID')
        if peal_id := validate_peal_input(peal_id):
            break
        else:
            error('Invalid Bellboard URL or peal ID')

    return peal_id


def validate_peal_input(id_or_url: str) -> int:
    if id_or_url.isnumeric():
        return int(id_or_url)
    else:
        return get_id_from_url(id_or_url)


def initialize_or_exit(reset_db: bool, clear_data: bool):
    if not initialize_db(reset_db):
        error('Unable to connect to pypeal database')
        raise typer.Exit()
    if reset_db:
        update_associations()
        update_towers()
        update_bells()
        update_methods()
    if clear_data:
        Peal.clear_data()
        Ringer.clear_data()


def get_peal_list():
    if not __peals:
        update_peal_list()
    return __peals


def update_peal_list():
    global __peals
    __peals = Peal.get_all()
