from datetime import datetime
import logging
from typing import Annotated
import webbrowser
import typer

from rich import print

from pypeal.bellboard.interface import BellboardError, get_id_from_url, get_url_from_id
from pypeal.bellboard.search import BellboardSearchNoResultFoundError, search as bellboard_search, search_by_url as bellboard_search_by_url
from pypeal.bellboard.html_generator import HTMLPealGenerator
from pypeal.cccbr import update_methods
from pypeal.cli.peal_prompter import PealPromptListener
from pypeal.cli.peal_previewer import PealPreviewListener
from pypeal.cli.prompts import UserCancelled, ask_date, choose_option, ask, confirm, panel, error
from pypeal.db import initialize as initialize_db
from pypeal.dove import update_associations, update_bells, update_towers
from pypeal.peal import Peal, PealType
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
            panel(f'Number of peals: {len(get_peal_list(force_update=True))}')

            match choose_option(['Add peal by URL',
                                 'Add random peal',
                                 'Add peal by search',
                                 'Add peal by search URL',
                                 'View peal',
                                 'Update static data',
                                 'Exit'],
                                default=1):
                case 1:
                    add_peal(prompt_peal_id(peal_id_or_url))
                case 2:
                    add_peal()
                case 3:
                    search()
                case 4:
                    search_by_url()
                case 5:
                    run_view(peal_id_or_url)
                case 6:
                    update_methods()
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

    generator = HTMLPealGenerator()
    preview_listener = PealPreviewListener()
    prompt_listener = PealPromptListener()

    try:
        generator.download(peal_id)
        generator.parse(preview_listener)
        panel(preview_listener.text, title=get_url_from_id(peal_id))
        generator.parse(prompt_listener)
    except BellboardError as e:
        logger.exception('Error getting peal from Bellboard: %s', e)
        error(e)
        return

    peal = prompt_listener.peal
    panel(str(peal), title=get_url_from_id(peal.bellboard_id))
    if confirm('Save this peal?'):
        peal.commit()
        print(f'Peal {peal.bellboard_id} added')


def search_by_url():

    while True:

        try:
            count_duplicate = 0
            count_added = 0
            for peal_id in bellboard_search_by_url(ask('Bellboard URL')):
                if peal_id in get_peal_list():
                    count_duplicate += 1
                    continue
                else:
                    if count_added > 0 and not confirm(None, confirm_message='Add next peal?'):
                        break
                    add_peal(peal_id)
                    count_added += 1
            print(f'{count_added} peal(s) added ({count_duplicate} duplicates)')

        except BellboardSearchNoResultFoundError as e:
            error(e)
            if confirm(None, confirm_message='Amend search in browser?'):
                webbrowser.open(e.url + '&edit')
                continue
        except BellboardError as e:
            error(e)
            search()
        break


def search():

    print('Enter search criteria.')
    print('% for wildcards, " for absolute match')
    name = ask('Ringer name', required=False)
    date_from = ask_date('Date from (yyyy-mm-dd)', max=datetime.now(), required=False)
    date_to = ask_date('Date to (yyyy-mm-dd)', min=date_from, max=datetime.now(), required=False)
    place = ask('Place', required=False)
    county = ask('County/Region/Country', required=False)
    dedication = ask('Dedication', required=False)
    association = ask('Association', required=False)
    title = ask('Title', required=False)
    type = choose_option(['Any', 'Tower', 'Handbells'],
                         values=[None, PealType.TOWER, PealType.HANDBELLS],
                         prompt='Type',
                         required=False,
                         default='Any')

    try:
        count_duplicate = 0
        count_added = 0
        for peal_id in bellboard_search(ringer_name=name,
                                        date_from=date_from,
                                        date_to=date_to,
                                        place=place,
                                        county=county,
                                        dedication=dedication,
                                        association=association,
                                        title=title,
                                        type=type):
            if peal_id in get_peal_list():
                count_duplicate += 1
                continue
            else:
                if count_added > 0 and not confirm(None, confirm_message='Add next peal?'):
                    break
                add_peal(peal_id)
                count_added += 1
        print(f'{count_added} peal(s) added ({count_duplicate} duplicates)')
    except BellboardSearchNoResultFoundError as e:
        error(e)
        if confirm(None, confirm_message='Amend search in browser?'):
            webbrowser.open(e.url + '&edit')
            search_by_url()
    except BellboardError as e:
        error(e)


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


def get_peal_list(force_update: bool = False):
    if not __peals or force_update:
        update_peal_list()
    return __peals


def update_peal_list():
    global __peals
    __peals = Peal.get_all()
