import logging
from typing import Annotated
import typer

from rich import print
from rich.table import Table

from pypeal.entities.association import Association

from pypeal.cccbr import update_methods
from pypeal.cli.prompt_delete_peal import prompt_delete_peal
from pypeal.cli.prompt_import_peal import add_peal, prompt_import_peal
from pypeal.cli.manual_generator import ManualGenerator
from pypeal.cli.prompt_report_stats import prompt_report
from pypeal.cli.prompts import UserCancelled, ask_int, confirm, format_timestamp, heading, panel, error, prompt_peal_id
from pypeal.cli.chooser import choose_option
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
from pypeal.stats.report import generate_summary as generate_peal_summary
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
        case 'report':
            run_generate_reports()
        case _:
            error(f'Unknown action: {action}')


def run_poll():
    poll()


def run_import_peal(peal_id_or_url: str):
    prompt_import_peal(prompt_peal_id(peal_id_or_url, required=False))


def run_view(peal_id_or_url: str):
    match choose_option(['Bellboard ID/URL', 'Peal ID'], default=1) if not peal_id_or_url else 1:
        case 1:
            panel(str(Peal.get(bellboard_id=prompt_peal_id(peal_id_or_url))))
        case 2:
            panel(str(Peal.get(id=ask_int('Peal ID', min=1, required=True))))
    confirm(None, 'Continue?')


def run_delete(peal_id_or_url: str):
    prompt_delete_peal(peal_id_or_url)


def run_add_peal():
    add_peal(ManualGenerator())


def run_generate_reports():
    print('Generating reports...')
    for report_path in generate_reports():
        print(f'- {report_path}')


def run_interactive(peal_id_or_url: str):

    while True:
        try:
            print_summary()

            try:
                selected_option = choose_option(
                    [
                        'BellBoard search',
                        'Add peal by ID/URL',
                        'Add peal manually',
                        'View statistics',
                        'Generate reports',
                        'View peal',
                        'Delete peal',
                        'Update static data'
                    ],
                    none_option='Exit',
                    default=1)
            except UserCancelled:
                raise typer.Exit()

            match selected_option:
                case 1:
                    prompt_search()
                case 2:
                    run_import_peal(peal_id_or_url)
                case 3:
                    run_add_peal()
                case 4:
                    prompt_report()
                case 5:
                    run_generate_reports()
                case 6:
                    run_view(peal_id_or_url)
                case 7:
                    run_delete(peal_id_or_url)
                case 8:
                    update_methods()
                    update_associations()
                    update_towers()
                    update_bells()
                case _:
                    raise typer.Exit()
        except UserCancelled:
            continue

        peal_id_or_url = None


def print_summary():
    heading('pypeal Database')
    summary = generate_peal_summary(Peal.get_all())
    if summary['count'] > 0:
        table = Table(show_header=False, show_footer=False, expand=True, box=None)
        table.add_column(ratio=1)
        table.add_column(ratio=1, justify='right')
        type_summary = ''
        last_updated = f'Last updated: {format_timestamp(summary["last_added"])}'
        for type, report in summary["types"].items():
            type_summary = f'{type} count: {report["count"]}\n'
            table.add_row(type_summary.strip(), last_updated)
            last_updated = ''
        print(table)


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
