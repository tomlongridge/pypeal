from datetime import datetime, timedelta
import logging
import webbrowser

from rich import print

from pypeal import utils
from pypeal.bellboard.interface import BellboardError
from pypeal.bellboard.search import BellboardSearchNoResultFoundError, search as bellboard_search
from pypeal.cli.prompt_add_tower import prompt_find_tower
from pypeal.cli.prompt_import_peal import prompt_import_peal
from pypeal.cli.prompts import UserCancelled, ask_date, ask, ask_int, confirm, error, format_timestamp, heading
from pypeal.cli.chooser import choose_option
from pypeal.entities.peal import Peal, BellType
from pypeal.entities.peal_search import PealSearch
from pypeal.parsers import parse_search_url

logger = logging.getLogger('pypeal')


def prompt_search():
    heading('Search BellBoard')
    while True:
        searches = PealSearch.get_all()
        try:
            selected_option = choose_option(['Run saved search',
                                             'New search',
                                             'Edit search',
                                             'Delete search',
                                             'Poll for new peals'],
                                            none_option='Back',
                                            default=1) if len(searches) > 0 else 2
        except UserCancelled:
            return
        try:
            match selected_option:
                case 1:
                    _search(choose_option(searches, none_option='New search'))
                case 2:
                    _search()
                case 3:
                    _search(choose_option(searches, none_option='Back'), prompt=True)
                case 4:
                    _delete_search(choose_option(searches, none_option='Back'))
                    if len(searches) == 0:
                        break
                case 5:
                    poll(run_all=True)
                case _:
                    break
        except UserCancelled:
            if len(searches) == 0:  # There are no other options, exit the menu
                break
            else:
                continue


def poll(run_all: bool = False):
    print('Polling for new peals...')
    for search in PealSearch.get_all():
        if search.poll_frequency:
            if run_all or search.last_run_date < utils.get_now() - timedelta(days=search.poll_frequency):
                print(f'Polling for new peals matching search "{search.description}"...')
                _search(search)
            else:
                print(f'Skipping search "{search.description}" (last run {format_timestamp(search.last_run_date)})')


def _search(peal_search: PealSearch = None, prompt: bool = False):

    if peal_search is None:
        heading('New peal search')
        peal_search = PealSearch()

    while True:

        if peal_search.id is None or prompt:

            match choose_option(['Enter criteria', 'Enter Bellboard URL'], none_option='Back', default=1) if peal_search.id is None else 1:
                case 1:
                    _create_search(peal_search)
                case 2:
                    while True:
                        try:
                            peal_search = parse_search_url(ask('Bellboard URL', required=True))
                            break
                        except ValueError as e:
                            error(e)
                            continue
                case _:
                    raise UserCancelled()

        try:
            count_duplicate = 0
            count_added = 0
            for peal_id, _ in bellboard_search(ringer_name=peal_search.ringer_name,
                                               date_from=peal_search.date_from,
                                               date_to=peal_search.date_to,
                                               dove_tower_id=peal_search.tower_id,
                                               place=peal_search.place,
                                               region=peal_search.region,
                                               address=peal_search.address,
                                               association=peal_search.association,
                                               title=peal_search.title,
                                               bell_type=peal_search.bell_type,
                                               order_by_submission_date=peal_search.order_by_submission_date,
                                               order_descending=peal_search.order_descending):

                if Peal.get(bellboard_id=peal_id):
                    count_duplicate += 1
                    continue
                else:
                    if count_added > 0 and not confirm(None, confirm_message='Add next peal?'):
                        break
                    if prompt_import_peal(peal_id):
                        count_added += 1

            print(f'{count_added} peal(s) added ({count_duplicate} duplicates)')
            peal_search.record_run()
            break

        except BellboardSearchNoResultFoundError as e:
            if peal_search.id is None or prompt:
                error(e)
                match choose_option(['Amend search', 'View search on BellBoard', 'New search'], none_option='Back'):
                    case 1:
                        pass
                    case 2:
                        webbrowser.open(e.url + '&edit')
                    case 3:
                        peal_search = PealSearch()
                    case _:
                        break
            else:
                break  # Don't error for a regular poll

        except BellboardError as e:
            error(e)
            return

    if (peal_search.id is None or prompt) and confirm(None, confirm_message='Save search?'):
        peal_search.description = ask('Description', default=peal_search.description, required=True)
        if confirm(None, confirm_message='Include in poll?', default=peal_search.poll_frequency is not None):
            peal_search.poll_frequency = ask_int('Poll frequency (days)', default=peal_search.poll_frequency, required=True)
        peal_search.commit()


def _create_search(peal_search: PealSearch):
    print('% for wildcards, " for absolute match')
    peal_search.ringer_name = ask('Ringer name',
                                  default=peal_search.ringer_name,
                                  required=False)
    peal_search.date_from = ask_date('Date from',
                                     default=peal_search.date_from,
                                     max=datetime.date(utils.get_now()),
                                     required=False)
    peal_search.date_to = ask_date('Date to',
                                   default=peal_search.date_to,
                                   min=peal_search.date_from,
                                   max=datetime.date(utils.get_now()),
                                   required=False)
    peal_search.association = ask('Association',
                                  default=peal_search.association,
                                  required=False)
    if tower := prompt_find_tower():
        peal_search.tower_id = tower.id * -1
    peal_search.place = ask('Place',
                            default=peal_search.place,
                            required=False) if not peal_search.tower_id else None
    peal_search.region = ask('County/Region/Country',
                             default=peal_search.region,
                             required=False) if not peal_search.tower_id else None
    peal_search.address = ask('Dedication',
                              default=peal_search.address,
                              required=False) if not peal_search.tower_id else None
    peal_search.title = ask('Title',
                            default=peal_search.title,
                            required=False)
    peal_search.bell_type = choose_option(['Tower', 'Handbells'],
                                          values=[BellType.TOWER, BellType.HANDBELLS],
                                          title='Type',
                                          none_option='Any',
                                          default=peal_search.bell_type)
    peal_search.order_by_submission_date = choose_option(['Date rung', 'Date submitted'],
                                                         values=[False, True],
                                                         title='Order by',
                                                         default=2 if peal_search.order_by_submission_date else 1)
    peal_search.order_descending = choose_option(['Newest', 'Oldest'],
                                                 values=[True, False],
                                                 title='Order of results',
                                                 default=2 if peal_search.order_descending else 1)


def _delete_search(peal_search: PealSearch):
    if confirm(f'Delete search "{peal_search}"?', default=False):
        peal_search.delete()
