from datetime import datetime, timedelta
import logging
from typing import Annotated
import webbrowser
import typer
import urllib.parse

from rich import print
from pypeal import config

from pypeal.bellboard.interface import BellboardError, get_id_from_url, get_url_from_id
from pypeal.bellboard.search import BellboardSearchNoResultFoundError, search as bellboard_search, search_by_url as bellboard_search_by_url
from pypeal.bellboard.html_generator import HTMLPealGenerator
from pypeal.cccbr import update_methods
from pypeal.cli.peal_prompter import PealPromptListener
from pypeal.cli.peal_previewer import PealPreviewListener
from pypeal.cli.prompt_commit_peal import prompt_commit_peal
from pypeal.cli.prompts import UserCancelled, ask_date, ask_int, ask, confirm, panel, error
from pypeal.cli.chooser import choose_option
from pypeal.db import initialize as initialize_db
from pypeal.dove import update_associations, update_bells, update_rings, update_towers
from pypeal.peal import Peal, BellType
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

            try:
                selected_option = choose_option(
                    [
                        'Find recent peals',
                        'Add peals by search',
                        'Add peals by search URL',
                        'Add peal by ID/URL',
                        'Add random peal',
                        'View peal',
                        'Update static data',
                        'Exit'
                    ],
                    default=1)
            except UserCancelled:
                raise typer.Exit()

            match selected_option:
                case 1:
                    poll_for_new_peals()
                case 2:
                    search()
                case 3:
                    search_by_url()
                case 4:
                    add_peal(prompt_peal_id(peal_id_or_url))
                case 5:
                    add_peal()
                case 6:
                    run_view(peal_id_or_url)
                case 7:
                    update_methods()
                    update_associations()
                    update_towers()
                    update_bells()
                case 8 | None:
                    raise typer.Exit()
        except UserCancelled:
            continue

        peal_id_or_url = None


def poll_for_new_peals():
    search_urls = config.get_config('bellboard', 'searches')
    if search_urls is None:
        error('No search URLs configured')
        return
    for url in search_urls:
        search_url = url.split('?')[0] + '?'
        params = urllib.parse.parse_qs(url.split('?')[1])
        for key, value in params.items():
            if key not in ['date_from', 'date_to']:
                search_url += f'&{key}={value[0] if value else ""}'
        search_url += '&date_from=' + (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        search_by_url(search_url)


def add_peal(peal_id: int = None):

    generator = HTMLPealGenerator()
    preview_listener = PealPreviewListener()
    prompt_listener = PealPromptListener()

    try:
        peal_id = generator.download(peal_id)
        generator.parse(preview_listener)
        panel(preview_listener.text, title=get_url_from_id(peal_id))

        if peal_id in get_peal_list():
            error(f'Peal {peal_id} already added to database')
            return

        prompt_listener.quick_mode = confirm(None, confirm_message='Try for a quick-add?', default=True)

        while True:
            generator.parse(prompt_listener)

            peal = prompt_listener.peal
            if not prompt_commit_peal(peal) and \
                    prompt_listener.quick_mode and \
                    confirm(None, confirm_message='Try again in prompt mode?', default=True):
                prompt_listener.quick_mode = False
                continue
            return

    except BellboardError as e:
        logger.exception('Error getting peal from Bellboard: %s', e)
        error(e)
        return


def search_by_url(url: str = None):

    while True:
        try:
            count_duplicate = 0
            count_added = 0
            for peal_id in bellboard_search_by_url(url or ask('Bellboard URL')):
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
    date_from = ask_date('Date from (yyyy-mm-dd)', max=datetime.date(datetime.now()), required=False)
    date_to = ask_date('Date to (yyyy-mm-dd)', min=date_from, max=datetime.date(datetime.now()), required=False)
    association = ask('Association', required=False)
    tower_id = ask_int('Dove Tower ID', required=False)
    place = ask('Place', required=False) if not tower_id else None
    county = ask('County/Region/Country', required=False) if not tower_id else None
    dedication = ask('Dedication', required=False) if not tower_id else None
    title = ask('Title', required=False)
    bell_type = choose_option(['Any', 'Tower', 'Handbells'],
                              values=[None, BellType.TOWER, BellType.HANDBELLS],
                              title='Type',
                              default=1)
    order_descending = choose_option(['Newest', 'Oldest'],
                                     values=[True, False],
                                     title='Order of results',
                                     default=1)

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
                                        bell_type=bell_type,
                                        order_descending=order_descending):
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
        update_rings()
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
    __peals = {peal.bellboard_id: peal for peal in Peal.get_all()}
