from datetime import datetime, timedelta
import logging
import webbrowser
import urllib.parse

from rich import print

from pypeal import config

from pypeal.bellboard.interface import BellboardError
from pypeal.bellboard.search import BellboardSearchNoResultFoundError, search as bellboard_search, search_by_url as bellboard_search_by_url
from pypeal.cli.prompt_import_peal import prompt_import_peal
from pypeal.cli.prompts import ask_date, ask_int, ask, confirm, error
from pypeal.cli.chooser import choose_option
from pypeal.peal import Peal, BellType

logger = logging.getLogger('pypeal')


def search_by_url(url: str = None):

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
                if Peal.get(bellboard_id=peal_id):
                    count_duplicate += 1
                    continue
                else:
                    if count_added > 0 and not confirm(None, confirm_message='Add next peal?'):
                        break
                    prompt_import_peal(peal_id)
                    count_added += 1
            print(f'{count_added} peal(s) added ({count_duplicate} duplicates)')

        except BellboardSearchNoResultFoundError as e:
            error(e)
            if confirm(None, confirm_message='Amend search in browser?'):
                webbrowser.open(e.url + '&edit')
                continue
        except BellboardError as e:
            error(e)
            prompt_search_peals()
        break


def prompt_search_peals():

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
            if Peal.get(bellboard_id=peal_id):
                count_duplicate += 1
                continue
            else:
                if count_added > 0 and not confirm(None, confirm_message='Add next peal?'):
                    break
                prompt_import_peal(peal_id)
                count_added += 1
        print(f'{count_added} peal(s) added ({count_duplicate} duplicates)')
    except BellboardSearchNoResultFoundError as e:
        error(e)
        if confirm(None, confirm_message='Amend search in browser?'):
            webbrowser.open(e.url + '&edit')
            search_by_url()
    except BellboardError as e:
        error(e)


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
