import datetime
from pypeal import utils
from pypeal.bellboard.utils import get_url_from_id
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.utils import format_date_full, get_bell_label


class PealPreviewListener(PealGeneratorListener):

    def __init__(self):
        self.__lines = None

    def new_peal(self, id: int):
        self.__lines = {}
        self.__lines['id'] = id

    def association(self, value: str):
        if value:
            self.__lines['association'] = value

    def location(self, address_dedication: str, place: str, county: str, country: str):
        self.__lines['location'] = f'{address_dedication}, ' if address_dedication else ''
        self.__lines['location'] += f'{place or "[no place]"}, {county or "[no county]"}'
        self.__lines['location'] += f', {country}' if country else ''

    def changes(self, value: int):
        self.__lines['title'] = f'{value} ' if value else ''

    def title(self, value: str):
        if 'title' not in self.__lines:
            self.__lines['title'] = ''
        self.__lines['title'] += utils.strip_internal_space(value)

    def method_details(self, value: str):
        if value:
            self.__lines['method_details'] = value

    def composition_details(self, name: str, url: str, note: str):
        if name:
            self.__lines['composer'] = name

    def date(self, value: datetime.date):
        self.__lines['date'] = format_date_full(value)

    def tenor(self, value: str):
        if value:
            self.__lines['date'] += f' ({value})'

    def duration(self, value: str):
        if value:
            self.__lines['date'] += f' in {value}'

    def ringer(self, name: str, nums: list[int], bells: list[int], is_conductor: bool):
        if 'ringers' not in self.__lines:
            self.__lines['ringers'] = []
        ringer_line = ''
        if nums:
            ringer_line += get_bell_label(nums)
            ringer_line += f' [{get_bell_label(bells)}]' if bells and nums != bells else ''
            ringer_line += ': '
        ringer_line += name
        if is_conductor:
            ringer_line += ' (c)'
        self.__lines['ringers'].append(ringer_line)

    def footnote(self, value: str):
        if value and len(value.strip()) > 0:
            if 'footnotes' not in self.__lines:
                self.__lines['footnotes'] = ''
            self.__lines['footnotes'] += f'{value}\n'

    def event(self, url: str):
        if url:
            self.__lines['event'] = url

    def photo(self, url: str, caption: str, credit: str):
        if url:
            self.__lines['photo'] = url

    def bellboard_metadata(self, submitter: str, date: datetime.date):
        self.__lines['bb_metadata'] = {}
        self.__lines['bb_metadata']['submitter'] = submitter or 'unknown'
        self.__lines['bb_metadata']['date'] = date

    def external_reference(self, value: str):
        self.__lines['external_reference'] = value

    @property
    def text(self) -> str:
        text = ''
        text += (self.__lines['association'] + '\n') if 'association' in self.__lines else ''
        text += (self.__lines['location'] + '\n') if 'location' in self.__lines else ''
        text += (self.__lines['title'] + '\n') if 'title' in self.__lines else ''
        text += (self.__lines['method_details'] + '\n') if 'method_details' in self.__lines else ''
        text += f'Composer: {self.__lines["composer"]}\n' if 'composer' in self.__lines else ''
        text += (self.__lines['date'] + '\n') if 'date' in self.__lines else ''
        text += '\n'
        for ringer in self.__lines['ringers']:
            text += f'{ringer}\n'
        text += '\n'
        if 'footnotes' in self.__lines:
            text += (self.__lines['footnotes'])
            text += '\n'
        text += (f'Linked event: {self.__lines["event"]}\n') if 'event' in self.__lines else ''
        text += f'Bellboard: {get_url_from_id(self.__lines["id"])}' if self.__lines['id'] else ''
        if 'bb_metadata' in self.__lines:
            text += f' (submitted by {self.__lines["bb_metadata"]["submitter"]}'
            text += f' on {utils.format_date_full(self.__lines["bb_metadata"]["date"])}' if self.__lines["bb_metadata"]["date"] else ''
            text += ')'
        text += '\n'
        text += (f'Photo: {self.__lines["photo"]}\n') if 'photo' in self.__lines else ''
        text += (f'External reference: {self.__lines["external_reference"]}\n') if 'external_reference' in self.__lines else ''
        return text.strip()

    @property
    def data(self) -> dict:
        return self.__lines

    @property
    def metadata(self) -> tuple[str, datetime.date]:
        if 'bb_metadata' in self.__lines:
            return self.__lines['bb_metadata']['submitter'], self.__lines['bb_metadata']['date']
