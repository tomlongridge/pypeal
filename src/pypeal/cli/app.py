from datetime import datetime, timedelta
import logging
from typing import Annotated
import webbrowser
import typer
import urllib.parse

from rich import print
from rich.table import Table

from pypeal import config

from pypeal.bellboard.interface import BellboardError, get_id_from_url, get_url_from_id
from pypeal.bellboard.search import BellboardSearchNoResultFoundError, search as bellboard_search, search_by_url as bellboard_search_by_url
from pypeal.bellboard.html_generator import HTMLPealGenerator
from pypeal.cccbr import update_methods
from pypeal.cli.generator import PealGenerator
from pypeal.cli.manual_generator import ManualGenerator
from pypeal.cli.peal_prompter import PealPromptListener
from pypeal.cli.peal_previewer import PealPreviewListener
from pypeal.cli.prompt_commit_peal import prompt_commit_peal
from pypeal.cli.prompt_report_stats import prompt_report_stats
from pypeal.cli.prompts import UserCancelled, ask_date, ask_int, ask, confirm, heading, panel, error
from pypeal.cli.chooser import choose_option
from pypeal.db import initialize as initialize_db
from pypeal.dove import update_associations, update_bells, update_rings, update_towers
from pypeal.peal import Peal, BellType
from pypeal.ringer import Ringer
from pypeal.config import get_config, set_config_file
from pypeal.stats.report import generate_summary as generate_peal_summary

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


_peals: dict[int, Peal] = None
_bb_peals: dict[str, Peal] = None


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

    refresh_peal_list()

    match action:
        case None:
            run_interactive(peal_id_or_url)
        case 'import':
            run_import_peal(peal_id_or_url)
        case 'add':
            run_add_peal(peal_id_or_url)
        case 'view':
            run_view(peal_id_or_url)
        case 'delete':
            run_delete(peal_id_or_url)
        case _:
            error(f'Unknown action: {action}')


def run_import_peal(peal_id_or_url: str):
    import_peal(prompt_peal_id(peal_id_or_url))


def run_view(peal_id_or_url: str):
    match choose_option(['Bellboard ID/URL', 'Peal ID'], default=1) if not peal_id_or_url else 1:
        case 1:
            panel(str(Peal.get(bellboard_id=prompt_peal_id(peal_id_or_url))))
        case 2:
            panel(str(Peal.get(id=ask_int('Peal ID', min=1, required=True))))
    confirm(None, 'Continue?')


def run_delete(peal_id_or_url: str):
    match choose_option(['Bellboard ID/URL', 'Peal ID'], default=1) if not peal_id_or_url else 1:
        case 1:
            peal_id = prompt_peal_id(peal_id_or_url)
            peal = Peal.get(bellboard_id=peal_id)
            panel(str(peal))
            delete_peal(peal.id)
        case 2:
            peal_id = ask_int('Peal ID', min=1, required=True)
            panel(str(Peal.get(id=peal_id)))
            delete_peal(peal_id)
    if not confirm(None, 'Continue?'):
        return


def run_add_peal():
    add_peal(ManualGenerator())


def run_interactive(peal_id_or_url: str):

    while True:
        try:
            print_summary()

            try:
                selected_option = choose_option(
                    [
                        'Find recent peals',
                        'Add peals by search',
                        'Add peals by search URL',
                        'Add peal by ID/URL',
                        'Add random peal from BellBoard',
                        'Add peal manually',
                        'View peal',
                        'View statistics',
                        'Delete peal',
                        'Update static data'
                    ],
                    none_option='Exit',
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
                    run_import_peal(peal_id_or_url)
                case 5:
                    import_peal()
                case 6:
                    run_add_peal()
                case 7:
                    run_view(peal_id_or_url)
                case 8:
                    prompt_report_stats()
                case 9:
                    run_delete(peal_id_or_url)
                case 10:
                    update_methods()
                    update_associations()
                    update_towers()
                    update_bells()
                case 11 | None:
                    raise typer.Exit()
        except UserCancelled:
            continue

        peal_id_or_url = None


def print_summary():
    global _peals
    heading('pypeal Database')
    summary = generate_peal_summary(_peals.values())
    if summary['count'] > 0:
        table = Table(show_header=False, show_footer=False, expand=True, box=None)
        table.add_column(ratio=1)
        table.add_column(ratio=1, justify='right')
        type_summary = ''
        last_updated = f'Last updated: {summary["last_added"]}' if not get_config('diagnostics', 'print_user_input') else ''
        for type, report in summary["types"].items():
            type_summary = f'{type} count: {report["count"]}\n'
            table.add_row(type_summary.strip(), last_updated)
            last_updated = ''
        print(table)


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


def import_peal(peal_id: int = None) -> Peal:
    global _bb_peals

    generator = HTMLPealGenerator()
    preview_listener = PealPreviewListener()

    try:
        peal_id = generator.download(peal_id)
        generator.parse(preview_listener)
        panel(preview_listener.text, title=get_url_from_id(peal_id))

        if peal_id in _bb_peals and \
                not confirm(f'Peal {peal_id} already added to database', confirm_message='Overwrite?', default=False):
            return

        return add_peal(generator)

    except BellboardError as e:
        logger.exception('Error getting peal from Bellboard: %s', e)
        error(e)


def add_peal(generator: PealGenerator) -> Peal:

    prompt_listener = PealPromptListener()
    prompt_listener.quick_mode = confirm(None, confirm_message='Try for a quick-add?', default=True)

    peal: Peal = None
    while True:

        try:
            generator.parse(prompt_listener)
        except UserCancelled:
            if confirm(None, confirm_message='Retry entire peal?', default=True):
                prompt_listener.quick_mode = False
                continue

        peal = prompt_listener.peal

        peal_saved, replaced_peal_id = prompt_commit_peal(peal)
        if peal_saved:
            update_peal_list(peal, replaced_peal_id)
            break
        elif prompt_listener.quick_mode and \
                confirm(None, confirm_message='Try again in prompt mode?', default=True):
            prompt_listener.quick_mode = False
            continue
        else:
            break

    return peal


def delete_peal(peal_id: int):
    peal = Peal.get(peal_id)
    if peal:
        peal.delete()
        update_peal_list(None, peal_id)


def search_by_url(url: str = None):
    global _bb_peals

    saved_searches = config.get_config('bellboard', 'searches')
    if url is None and saved_searches:
        url = choose_option(saved_searches,
                            values=saved_searches,
                            title='Use saved search?',
                            none_option='Enter URL',
                            default=1)

    if url is None:
        url = ask('Bellboard URL', required=True)

    while True:
        try:
            count_duplicate = 0
            count_added = 0
            for peal_id in bellboard_search_by_url(url):
                if peal_id in _bb_peals:
                    count_duplicate += 1
                    continue
                else:
                    if count_added > 0 and not confirm(None, confirm_message='Add next peal?'):
                        break
                    import_peal(peal_id)
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
    date_from = ask_date('Date from', max=datetime.date(datetime.now()), required=False)
    date_to = ask_date('Date to', min=date_from, max=datetime.date(datetime.now()), required=False)
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
    order_by_submission_date = choose_option(['Date submitted', 'Date rung'],
                                             values=[True, False],
                                             title='Order by',
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
                                        tower_id=tower_id,
                                        place=place,
                                        county=county,
                                        dedication=dedication,
                                        association=association,
                                        title=title,
                                        bell_type=bell_type,
                                        order_by_submission_date=order_by_submission_date,
                                        order_descending=order_descending):
            if peal_id in _bb_peals:
                count_duplicate += 1
                continue
            else:
                if count_added > 0 and not confirm(None, confirm_message='Add next peal?'):
                    break
                import_peal(peal_id)
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


def refresh_peal_list():
    global _peals, _bb_peals
    _peals = {peal.id: peal for peal in Peal.get_all()}
    _bb_peals = {peal.bellboard_id: peal for peal in _peals.values()}


def update_peal_list(new_peal: Peal = None, overwrite_peal_id: int = None):
    global _peals, _bb_peals
    if new_peal:
        _peals[new_peal.id] = new_peal
        if new_peal.bellboard_id:
            _bb_peals[new_peal.bellboard_id] = new_peal
    if overwrite_peal_id:
        del _peals[overwrite_peal_id]
