import logging
from typing import Annotated
import typer

from rich import print
from rich.table import Table

from pypeal.cache import Cache
from pypeal.cli.prompt_csv_import import prompt_csv_import
from pypeal.cli.prompt_manual_peal import prompt_manual_peal
from pypeal.cli.prompt_peal_input import prompt_peal_input
from pypeal.cli.prompt_submit import prompt_submit_peal, prompt_submit_unpublished_peals
from pypeal.cli.prompt_view_peal import prompt_view_peal
from pypeal.entities.association import Association

from pypeal.cccbr import update_methods
from pypeal.cli.prompt_delete_peal import prompt_delete_peal
from pypeal.cli.prompt_import_peal import prompt_import_peal
from pypeal.cli.prompt_report_stats import prompt_report
from pypeal.cli.prompts import UserCancelled, format_timestamp, heading, error, press_any_key
from pypeal.cli.chooser import choose_option_in_dict
from pypeal.cli.prompt_search_peals import poll, prompt_search
from pypeal.db import initialize as initialize_db
from pypeal.dove import update_associations, update_bells, update_rings, update_towers
from pypeal.entities.method import Method
from pypeal.entities.peal import Peal
from pypeal.entities.peal_search import PealSearch
from pypeal.entities.report import Report
from pypeal.entities.ringer import Ringer
from pypeal.config import set_config_file
from pypeal.stats.pdf import generate_reports
from pypeal.stats.report import generate_global_summary
from pypeal.entities.tower import Ring, Tower

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
            run_poll()
            run_interactive(peal_id_or_url)
        case 'import':
            run_import_peal(peal_id_or_url)
        case 'add':
            run_add_peal(peal_id_or_url)
        case 'view':
            run_view(peal_id_or_url)
        case 'delete':
            run_delete(peal_id_or_url)
        case 'submit':
            run_submit_peal(peal_id_or_url)
        case 'report':
            run_generate_reports()
        case 'bulk_upload':
            run_bulk_upload()
        case _:
            error(f'Unknown action: {action}')


def run_poll():
    poll()


def run_import_peal(peal_id_or_url_or_file: int | str):
    for input in prompt_peal_input(peal_id_or_url_or_file, allow_file=True):
        if type(input) is int:
            prompt_import_peal(input)
        elif type(input) is str:
            prompt_csv_import(input)
        else:
            error(f'Unable to import peals from {peal_id_or_url_or_file}')


def run_view(peal_id_or_url: str):
    prompt_view_peal(peal_id_or_url)


def run_delete(peal_id_or_url: str):
    prompt_delete_peal(peal_id_or_url)


def run_submit_peal(peal_id_or_url: str):
    if peal_id_or_url.isnumeric():
        prompt_submit_peal(int(peal_id_or_url))
    else:
        error(f'Invalid database ID for peal: {peal_id_or_url}')


def run_add_peal():
    prompt_manual_peal()


def run_generate_reports():
    heading('Generate PDF reports')
    for report_path in generate_reports():
        print(f'- {report_path}')
    press_any_key()


def run_bulk_upload():
    prompt_submit_unpublished_peals(in_bulk=True)


def run_update_static_data():
    heading('Update static data')
    update_methods()
    update_associations()
    update_towers()
    update_bells()


def run_interactive(peal_id_or_url: str):

    while True:
        try:
            summary_data = get_summary()

            menu_options = {
                'BellBoard search': lambda: prompt_search(),
                'Add peal by ID/URL': lambda: run_import_peal(peal_id_or_url),
                'Add peal manually': lambda: run_add_peal(),
                'View statistics': lambda: prompt_report(),
                'Generate reports': lambda: run_generate_reports(),
                'View peal': lambda: run_view(peal_id_or_url),
                'Delete peal': lambda: run_delete(peal_id_or_url),
                'Update static data': lambda: run_update_static_data(),
                'Clear app cache': lambda: Cache.get_cache().clear_all(),
            }

            if summary_data['unsubmitted_count'] > 0:
                menu_options['Submit unsubmitted peals'] = lambda: prompt_submit_unpublished_peals()

            try:
                selected_option = choose_option_in_dict(menu_options, none_option='Exit', default='BellBoard search')
            except UserCancelled:
                raise typer.Exit()

            if selected_option is not None:
                selected_option()
            else:
                raise typer.Exit()
        except UserCancelled:
            continue

        peal_id_or_url = None


def get_summary() -> dict:
    heading('pypeal Database', full=True)
    summary = generate_global_summary(Peal.get_all())
    if summary['count'] > 0:
        table = Table(show_header=False, show_footer=False, expand=True, box=None)
        table.add_column(ratio=1)
        table.add_column(ratio=1, justify='right')
        last_updated = ''
        if summary['unsubmitted_count'] > 0:
            last_updated += f'Unsubmitted: {summary["unsubmitted_count"]}\n'
        last_updated += f'Last updated: {format_timestamp(summary["last_added"])}\n'
        type_summary = ''
        for type, count in summary["types"].items():
            type_summary += f'{type} count: {count}\n'
        table.add_row(type_summary.strip(), last_updated.strip())
        print(table)
    return summary


def initialize_or_exit(reset_db: bool, clear_data: bool):
    if not initialize_db(reset_db):
        error('Unable to connect to pypeal database')
        raise typer.Exit()
    if clear_data or reset_db:
        Report.clear_data()
        PealSearch.clear_data()
        Peal.clear_data()
        Ringer.clear_data()
        Ring.clear_data()
        Method.clear_data()
        Tower.clear_data()
        Association.clear_data()
    if reset_db:
        update_associations()
        update_towers()
        update_bells()
        update_rings()
        update_methods()
