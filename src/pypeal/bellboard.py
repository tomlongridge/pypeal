from datetime import datetime, timedelta
import re
import time
from bs4 import BeautifulSoup
import logging
from requests import Response, get as get_request
from requests.exceptions import RequestException

from pypeal.config import get_config
from pypeal.peal import Peal
from pypeal.ringer import Ringer

BELLBOARD_PEAL_ID_URL = '/view.php?id=%s'
BELLBOARD_PEAL_RANDOM_URL = '/view.php?random'
BELLBOARD_SEARCH_URL = '/search.php?ringer=%s'

DATE_LINE_INFO_REGEX = re.compile(r'[A-Za-z]+,\s(?P<date>[0-9]+\s[A-Za-z0-9]+\s[0-9]+)(?:\s' +
                                  r'in\s(?P<duration>[A-Za-z0-9\s]+))?\s?(?:\((?P<tenor_weight>[^in]+|size\s[0-9]+)' +
                                  r'(?:\sin\s(?P<tenor_tone>.*))?\))?$')
DURATION_REGEX = re.compile(r'^(?:(?P<hours>\d{1,2})[h])$|^(?:(?P<mins>\d+)[m]?)$|' +
                            r'^(?:(?:(?P<hours_2>\d{1,2})[h])\s(?:(?P<mins_2>(?:[0]?|[1-5]{1})[0-9])[m]?))$')

FOOTNOTE_RINGER_REGEX_PREFIX = re.compile(r'^(?P<bells>[0-9,\s]+)\s?[-:]\s(?P<footnote>.*)$')
FOOTNOTE_RINGER_REGEX_SUFFIX = re.compile(r'^(?P<footnote>.*)\s?[-:]\s(?P<bells>[0-9,\s]+)\.?$')

__last_call: datetime = None


class BellboardError(Exception):
    pass


logger = logging.getLogger('pypeal')


def get_url_from_id(id: int) -> str:
    return get_config('bellboard', 'url') + (BELLBOARD_PEAL_ID_URL % id if id else BELLBOARD_PEAL_RANDOM_URL)


def get_id_from_url(url: str) -> int:
    if url and url.startswith('http') and url.find('id=') != -1:
        return int(url.split('id=')[1].split('&')[0])
    else:
        return None


def get_peal(url: str = None) -> Peal:
    url, html = download_peal(url if url else get_config('bellboard', 'url') + BELLBOARD_PEAL_RANDOM_URL)
    return get_peal_from_html(get_id_from_url(url), html)


def get_peal_from_html(id: int, html: str) -> Peal:

    peal = Peal(id)
    soup = BeautifulSoup(html, 'html.parser')

    element = soup.select('div.association')
    peal.association = element[0].text.strip() if len(element) == 1 else None
    element = soup.select('span.place')
    peal.place = element[0].text.strip() if len(element) == 1 else None
    peal.county = element[0].next_sibling.text.strip(', ') if element[0].next_sibling else None
    element = soup.select('div.address')
    peal.address_dedication = element[0].text.strip() if len(element) == 1 else None
    element = soup.select('span.changes')
    peal.changes = int(element[0].text.strip()) if len(element) == 1 else None
    element = soup.select('span.title')
    peal.title = element[0].text.strip() if len(element) == 1 else None

    # The date line is the first line of the performance div that doesn't have a class
    date_line = None
    for peal_detail in soup.select('div.performance')[0].children:
        if not peal_detail.attrs or 'class' not in peal_detail.attrs:
            date_line = peal_detail.text.strip()
            break

    if not (date_line_match := re.match(DATE_LINE_INFO_REGEX, date_line)):
        raise BellboardError(f'Unable to parse date line: {date_line}')

    date_line_info = date_line_match.groupdict()
    peal.date = datetime.strptime(date_line_info['date'], '%d %B %Y')
    peal.tenor_weight = date_line_info['tenor_weight']
    peal.tenor_tone = date_line_info['tenor_tone']

    if date_line_info['duration']:
        if not (duration_match := re.search(DURATION_REGEX, date_line_info['duration'].strip())):
            raise BellboardError(f'Unable to parse date line: {date_line}')
        duration_info = duration_match.groupdict()
        peal.duration = int(duration_info['hours'] or 0) * 60
        peal.duration += int(duration_info['hours_2'] or 0) * 60
        peal.duration += int(duration_info['mins'] or 0)
        peal.duration += int(duration_info['mins_2'] or 0)

    # Get ringers and their bells and add them to the ringers list
    ringer_names = []
    conductors = []
    for ringer in soup.select('span.ringer.persona'):
        ringer_names.append(ringer.text)
        conductors.append(
            ringer.next_sibling and
            ringer.next_sibling.lower().strip() == '(c)')

    ringer_bells = [bell.text.strip() for bell in soup.select('span.bell')]
    if len(ringer_bells) == 0:
        # Accounting for performances with no assigned bells - ensure the zip iteration completes
        ringer_bells = [None] * len(ringer_names)

    # Loop over the ringers and their bell (or bells) and add them to the peal
    for full_name, bells, is_conductor in zip(ringer_names, ringer_bells, conductors):
        if bells is not None:
            bells = [int(bell) for bell in bells.split('–')]
        last_name = full_name.split(' ')[-1]
        given_names = ' '.join(full_name.split(' ')[:-1])
        peal.add_ringer(Ringer(last_name, given_names), bells, is_conductor)

    for footnote in soup.select('div.footnote'):
        text = footnote.text.strip()
        if len(text) > 0:
            if (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_PREFIX, text)) or \
               (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_SUFFIX, text)):
                footnote_info = footnote_match.groupdict()
                text = footnote_info['footnote'].strip()
                bells = [int(bell) for bell in footnote_info['bells'].split(',')]
            else:
                bells = [None]
            for bell in bells:
                peal.add_footnote(bell, text)

    return peal


def split_full_name(full_name: str) -> tuple[str, str]:
    last_name = full_name.split(' ')[-1]
    given_names = ' '.join(full_name.split(' ')[:-1])
    return last_name, given_names


def search(ringer: str):

    logger.info(f'Searching for "{ringer}" on BellBoard...')

    response: Response = request(get_config('bellboard', 'url') + BELLBOARD_SEARCH_URL % ringer)

    soup = BeautifulSoup(response.text, 'html.parser')

    peal_ids = soup.find('input', {'name': 'ids'}).get('value').split(',')

    logger.info(f'Found {len(peal_ids)} peals for {ringer} on BellBoard')

    return [get_peal(get_url_from_id(int(id))) for id in peal_ids[0:2]]


def download_peal(url: str) -> tuple[int, str]:

    logger.info(f'Getting peal at {url}')
    response = request(url)
    logger.info(f'Retrieved peal at {response[0]}')

    return response


def request(url: str) -> tuple[str, str]:

    # Rate-limit requests to avoid affecting BellBoard service
    global __last_call
    rate_limit_secs = int(get_config('bellboard', 'rate_limit_secs') or 1)
    if __last_call and __last_call < datetime.now() - timedelta(seconds=-rate_limit_secs):
        logger.info(f'Waiting {rate_limit_secs}s before making BellBoard request...')
        time.sleep(rate_limit_secs)
    __last_call = datetime.now()

    try:
        response: Response = get_request(url)
        response.raise_for_status()
        return (response.url, response.text)
    except RequestException as e:
        raise BellboardError(f'Unable to access {url}: {e}') from e
