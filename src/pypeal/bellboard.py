from datetime import datetime
import re
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
import logging
from requests import Response, get as get_request
from requests.exceptions import RequestException

DATE_LINE_INFO_REGEX = re.compile(r'[A-Za-z]+,\s(?P<date>[0-9]+\s[A-Za-z0-9]+\s[0-9]+)(?:\s' +
                                  r'in\s(?P<duration>[A-Za-z0-9\s]+))?\s?(?:\((?P<tenor_weight>[^in]+|size\s[0-9]+)' +
                                  r'(?:\sin\s(?P<tenor_tone>.*))?\))?$')
DURATION_REGEX = re.compile(r'^(?:(?P<hours>\d{1,2})[h])$|^(?:(?P<mins>\d+)[m]?)$|' +
                            r'^(?:(?:(?P<hours_2>\d{1,2})[h])\s(?:(?P<mins_2>(?:[0]?|[1-5]{1})[0-9])[m]?))$')


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
    url: str = None
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
        text = f'Peal {self.id} at {self.url}\n'
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
        return text


logger = logging.getLogger('pypeal')


def get_url(id: int) -> str:
    return f'https://bb.ringingworld.co.uk/view.php?id={id}' if id \
        else 'https://bb.ringingworld.co.uk/view.php?random'


def get_peal(id: int = None, html: str = None) -> BellboardPeal:

    url = get_url(id)

    if html is None:
        logger.info(f'Getting peal at {url}')

        try:
            response: Response = get_request(url)
            response.raise_for_status()
        except RequestException as e:
            raise BellboardError(f'Unable to get peal at {response.url}: {e}') from e

        url = response.url  # Get actual URL after redirect
        id = int(response.url.split('?id=')[1].split('&')[0])
        html = response.text
        logger.info(f'Retrieved peal at {url}')

    soup = BeautifulSoup(html, 'html.parser')

    peal = BellboardPeal()
    peal.id = id
    peal.url = url

    element = soup.select('div.association')
    peal.association = element[0].text.strip() if len(element) == 1 else None
    element = soup.select('span.place')
    peal.place = element[0].text.strip() if len(element) == 1 else None
    peal.county = element[0].next_sibling.text.strip(', ')
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
        peal.footnotes.append(footnote.text.strip())

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

    try:
        response: Response = get_request(f'https://bb.ringingworld.co.uk/search.php?ringer={ringer}')
        response.raise_for_status()
    except RequestException as e:
        raise BellboardError(f'Unable to search BellBoard for {ringer}: {e}') from e

    soup = BeautifulSoup(response.text, 'html.parser')

    peal_ids = soup.find('input', {'name': 'ids'}).get('value').split(',')

    logger.info(f'Found {len(peal_ids)} peals for {ringer} on BellBoard')

    return [get_peal(int(id)) for id in peal_ids[0:2]]
