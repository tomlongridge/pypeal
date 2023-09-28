from datetime import datetime, timedelta
import re
import time
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
import logging
from requests import Response, get as get_request
from requests.exceptions import RequestException

from pypeal.config import get_config

BELLBOARD_PEAL_ID_URL = '/view.php?id=%s'
BELLBOARD_PEAL_RANDOM_URL = '/view?random'
BELLBOARD_SEARCH_URL = '/search.php?ringer=%s'

DATE_LINE_INFO_REGEX = re.compile(r'[A-Za-z]+,\s(?P<date>[0-9]+\s[A-Za-z0-9]+\s[0-9]+)(?:\s' +
                                  r'in\s(?P<duration>[A-Za-z0-9\s]+))?\s?(?:\((?P<tenor_weight>[^in]+|size\s[0-9]+)' +
                                  r'(?:\sin\s(?P<tenor_tone>.*))?\))?$')
DURATION_REGEX = re.compile(r'^(?:(?P<hours>\d{1,2})[h])$|^(?:(?P<mins>\d+)[m]?)$|' +
                            r'^(?:(?:(?P<hours_2>\d{1,2})[h])\s(?:(?P<mins_2>(?:[0]?|[1-5]{1})[0-9])[m]?))$')


__last_call: datetime = None


class BellboardError(Exception):
    pass


@dataclass
class BellboardRinger():
    """Represents a ringer from a Bellboard peal."""
    name: str
    bells: list[int]
    is_conductor: bool = False

    def __str__(self) -> str:
        return self.name + (' (c)' if self.is_conductor else '')


@dataclass
class BellboardPeal:
    """Represents the data gathered from a Bellboard peal."""

    id: int = None
    date: datetime.date = None
    association: str = None
    place: str = None
    address_dedication: str = None
    county: str = None
    changes: int = None
    title: str = None
    duration: int = None
    tenor_weight: str = None
    tenor_tone: str = None
    location_dove_id: int = None
    ringers: dict[str, BellboardRinger] = field(default_factory=dict)  # name -> ringer map
    footnotes: list[str] = field(default_factory=list)

    ringers_by_bell: list[tuple[int, BellboardRinger]] = field(default_factory=list)  # For internal representation only

    def __str__(self):
        text = ''
        text += f'{self.association}\n' if self.association else ''
        text += f'{self.place}' if self.place else '<UNKNOWN PLACE>'
        text += f', {self.county}' if self.county else ''
        text += '\n'
        text += f'{self.address_dedication}\n' if self.address_dedication else ''
        text += f'on {self.date.strftime("%A, %-d %B %Y")}\n' if self.date else '<UNKNOWN DATE>\n'
        text += f'in {self.duration} mins\n' if self.duration else ''
        if self.tenor_weight:
            text += f'({self.tenor_weight}'
            text += f' in {self.tenor_tone}' if self.tenor_tone else ''
            text += ')\n'
        for ringer in self.ringers_by_bell:
            text += str(ringer[0]) + ' ' if ringer[0] else ''
            text += str(ringer[1]) + '\n'
        for footnote in self.footnotes:
            text += f'{footnote}\n'
        text += f'[Imported Bellboard peal ID: {self.id}]' if self.id else ''
        return text


logger = logging.getLogger('pypeal')


def get_url_from_id(id: int) -> str:
    return get_config('bellboard')['url'] + (BELLBOARD_PEAL_ID_URL % id if id else BELLBOARD_PEAL_RANDOM_URL)


def get_id_from_url(url: str) -> int:
    if url and url.startswith('http') and url.find('id=') != -1:
        return int(url.split('id=')[1].split('&')[0])
    else:
        return None


def get_peal(url: str = None, html: str = None) -> BellboardPeal:

    peal = BellboardPeal()

    if html is None:
        id, html = download_peal(url if url else get_config('bellboard')['url'] + BELLBOARD_PEAL_RANDOM_URL)
        peal.id = id

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

    for footnote in soup.select('div.footnote'):
        text = footnote.text.strip()
        if len(text) > 0:
            peal.footnotes.append(text)

    # Get ringers and their bells and add them to the ringers list
    ringers = []
    conductors = []
    for ringer in soup.select('span.ringer.persona'):
        ringers.append(ringer.text)
        conductors.append(
            ringer.next_sibling and
            ringer.next_sibling.lower().strip() == '(c)')

    ringer_bells = [bell.text.strip() for bell in soup.select('span.bell')]
    if len(ringer_bells) == 0:
        # Accounting for performances with no assigned bells - ensure the zip iteration completes
        ringer_bells = [None] * len(ringers)

    # Loop over the ringers and their bell (or bells) and add them to the name->ringer map
    for ringer, bells, is_conductor in zip(ringers, ringer_bells, conductors):
        if bells is None:
            peal.ringers[ringer] = BellboardRinger(ringer, [], is_conductor)
            peal.ringers_by_bell.append((None, peal.ringers[ringer]))
        else:
            for bell in bells.split('–'):
                if ringer not in peal.ringers:
                    peal.ringers[ringer] = BellboardRinger(ringer, [int(bell)], is_conductor)
                else:
                    peal.ringers[ringer].bells.append(int(bell))
                    peal.ringers[ringer].is_conductor |= is_conductor
                peal.ringers_by_bell.insert(int(bell), (int(bell), peal.ringers[ringer]))

    return peal


def search(ringer: str):

    logger.info(f'Searching for "{ringer}" on BellBoard...')

    response: Response = request(get_config('bellboard')['url'] + BELLBOARD_SEARCH_URL % ringer)

    soup = BeautifulSoup(response.text, 'html.parser')

    peal_ids = soup.find('input', {'name': 'ids'}).get('value').split(',')

    logger.info(f'Found {len(peal_ids)} peals for {ringer} on BellBoard')

    return [get_peal(int(id)) for id in peal_ids[0:2]]


def download_peal(url: str) -> tuple[int, str]:

    logger.info(f'Getting peal at {url}')
    response = request(url)
    logger.info(f'Retrieved peal at {response[0]}')

    return (get_id_from_url(response[0]), response[1])


def request(url: str) -> tuple[str, str]:

    # Rate-limit requests to avoid affecting BellBoard service
    global __last_call
    rate_limit_secs = int(get_config('bellboard')['rate_limit_secs'])
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
