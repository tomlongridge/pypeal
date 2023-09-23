from bs4 import BeautifulSoup
from dataclasses import dataclass
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
    conductor: bool = False

    def __str__(self) -> str:
        return self.name + (' (c)' if self.conductor else '')


@dataclass
class BellboardPeal:
    """Represents the data gathered from a Bellboard peal."""

    id: int
    url: str
    ringers: dict[str, BellboardRinger]  # name -> ringer map

    _ringers_by_bell: list[tuple[int, BellboardRinger]]  # For internal representation only

    def __init__(self, id: int = None):

        self.logger = logging.getLogger('pypeal')

        self.url: str = f'https://bb.ringingworld.co.uk/view.php?id={id}' if id \
            else 'https://bb.ringingworld.co.uk/view.php?random'

        self.logger.info(f'Getting peal at {self.url}')

        try:
            response: Response = get_request(self.url)
            response.raise_for_status()
        except RequestException as e:
            raise BellboardError(f'Unable to get peal at {response.url}: {e}') from e

        self.url = response.url  # Get actual URL after redirect
        self.logger.info(f'Retrieved peal at {self.url}')

        soup = BeautifulSoup(response.text, 'html.parser')
        self.id = int(response.url.split('?id=')[1].split('&')[0])

        # Get ringers and their bells and add them to the ringers list
        ringers = [ringer.text for ringer in soup.select('span.ringer.persona')]
        ringer_bells = [bell.text for bell in soup.select('span.bell')]
        if len(ringer_bells) == 0:
            # Accounting for performances with no assigned bells - ensure the zip iteration completes
            ringer_bells = [None] * len(ringers)

        # Loop over the ringers and their bell (or bells) and add them to the name->ringer map
        self.ringers = dict()
        self._ringers_by_bell = list()
        for ringer, bells in zip(ringers, ringer_bells):
            is_conductor = ringer.lower().endswith('(c)')
            if bells is None:
                self.ringers[ringer] = BellboardRinger(ringer, [], is_conductor)
                self._ringers_by_bell.append((None, self.ringers[ringer]))
            else:
                for bell in bells.split('–'):
                    if ringer not in self.ringers:
                        self.ringers[ringer] = BellboardRinger(ringer, [int(bell)], is_conductor)
                    else:
                        self.ringers[ringer].bells.append(int(bell))
                        self.ringers[ringer].conductor |= is_conductor
                    self._ringers_by_bell.insert(int(bell), (int(bell), self.ringers[ringer]))

    def __str__(self):
        text = f'Peal {self.id} at {self.url}\n'
        for ringer in self._ringers_by_bell:
            text += str(ringer[0]) + ' ' if ringer[0] else ''
            text += str(ringer[1]) + '\n'
        return text
