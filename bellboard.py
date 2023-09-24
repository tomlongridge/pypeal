from bs4 import BeautifulSoup
from dataclasses import dataclass, field
import logging
from requests import Response, get as get_request
from requests.exceptions import RequestException


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
    ringers: dict[str, BellboardRinger] = field(default_factory=dict)  # name -> ringer map

    ringers_by_bell: list[tuple[int, BellboardRinger]] = field(default_factory=list)  # For internal representation only

    def __str__(self):
        text = f'Peal {self.id} at {self.url}\n'
        for ringer in self.ringers_by_bell:
            text += str(ringer[0]) + ' ' if ringer[0] else ''
            text += str(ringer[1]) + '\n'
        return text


class BellboardSearcher:

    def __init__(self):
        self.logger = logging.getLogger('pypeal')

    def get_peal(self, id: int = None) -> BellboardPeal:

        url: str = f'https://bb.ringingworld.co.uk/view.php?id={id}' if id \
            else 'https://bb.ringingworld.co.uk/view.php?random'

        self.logger.info(f'Getting peal at {url}')

        try:
            response: Response = get_request(url)
            response.raise_for_status()
        except RequestException as e:
            raise BellboardError(f'Unable to get peal at {response.url}: {e}') from e

        url = response.url  # Get actual URL after redirect
        self.logger.info(f'Retrieved peal at {url}')

        soup = BeautifulSoup(response.text, 'html.parser')

        peal = BellboardPeal()
        peal.id = int(response.url.split('?id=')[1].split('&')[0])
        peal.url = url

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

    def search(self, ringer: str):

        self.logger.info(f'Searching for "{ringer}" on BellBoard...')

        try:
            response: Response = get_request(f'https://bb.ringingworld.co.uk/search.php?ringer={ringer}')
            response.raise_for_status()
        except RequestException as e:
            raise BellboardError(f'Unable to search BellBoard for {ringer}: {e}') from e

        soup = BeautifulSoup(response.text, 'html.parser')

        peal_ids = soup.find('input', {'name': 'ids'}).get('value').split(',')

        self.logger.info(f'Found {len(peal_ids)} peals for {ringer} on BellBoard')

        return [self.get_peal(int(id)) for id in peal_ids[0:2]]
