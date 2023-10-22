import logging
from typing import Annotated
import typer

from rich import print

from pypeal.bellboard.interface import get_id_from_url, get_url_from_id
from pypeal.bellboard.html_generator import HTMLPealGenerator
from pypeal.bellboard.xml_generator import XMLPealGenerator
from pypeal.cli.peal_prompter import PealPrompter
from pypeal.cli.prompts import choose_option, ask, confirm, panel, error
from pypeal.db import initialize as initialize_db
from pypeal.method import Method
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

        match choose_option(['Add peal by URL',
                             'Add random peal',
                             'Add peal by search',
                             'View method',
                             'Update methods',
                             'Exit'],
                            default=1):
            case 1:
                peal_id, bb_url = prompt_peal_id(peal_id_or_url)
                if peal_id in peals:
                    error(f'Peal {peal_id} already added')
                elif bb_url:
                    add_peal(bb_url)
            case 2:
                add_peal()
            case 3:
                search_peals()
            case 4:
                run_view(peal_id_or_url)
            case 5:
                Method.update()
            case 6 | None:
                raise typer.Exit()

        peal_id_or_url = None


def add_peal(url: str = None):

    listener = PealPrompter()
    generator = HTMLPealGenerator(listener)
    peal = generator.get(url)

    panel(str(peal), title=get_url_from_id(peal.bellboard_id))
    if confirm('Save this peal?'):
        peal.commit()
        print(f'Peal {peal.bellboard_id} added')


def search_peals():

    name: str = ask('Ringer name:')

    listener = PealPrompter()
    generator = XMLPealGenerator(listener)

    for peal in generator.search(name):
        panel(str(peal), title=get_url_from_id(peal.bellboard_id))
        if confirm('Save this peal?'):
            peal.commit()
            print(f'Peal {peal.bellboard_id} added')


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


def initialize_or_exit(reset_db: bool, clear_data: bool):
    if not initialize_db(reset_db):
        error('Unable to connect to pypeal database')
        raise typer.Exit()
    if reset_db:
        Method.update()
    if clear_data:
        Peal.clear_data()
        Ringer.clear_data()
