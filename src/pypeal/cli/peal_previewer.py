from datetime import datetime
from pypeal.bellboard.interface import get_url_from_id
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

    def location(self, address_dedication: str, place: str, county: str):
        self.__lines['location'] = f'{address_dedication}, {place or "[no place]"}, {county or "[no county]"}'

    def changes(self, value: int):
        self.__lines['title'] = f'{value} ' if value else ''

    def title(self, value: str):
        self.__lines['title'] += value

    def method_details(self, value: str):
        if value:
            self.__lines['method_details'] = value

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
            self.__lines['ringers'] = ''
        if nums:
            self.__lines['ringers'] += get_bell_label(nums)
            self.__lines['ringers'] += f' [{get_bell_label(bells)}]' if bells and nums != bells else ''
            self.__lines['ringers'] += ': '
        self.__lines['ringers'] += name
        if is_conductor:
            self.__lines['ringers'] += ' (c)'
        self.__lines['ringers'] += '\n'

    def footnote(self, value: str):
        if value and len(value.strip()) > 0:
            if 'footnotes' not in self.__lines:
                self.__lines['footnotes'] = ''
            self.__lines['footnotes'] += f'{value}\n'

    def event(self, url: str):
        if url:
            self.__lines['event'] = url

    def bellboard_metadata(self, submitter: str, date: date):
        self.__lines['bb_metadata'] = f'submitted by {submitter or "Unknown"}'
        self.__lines['bb_metadata'] += f' on {format_date_full(date)}' if date else ''

    def external_reference(self, value: str):
        self.__lines['external_reference'] = value

    @property
    def text(self) -> str:
        text = ''
        text += (self.__lines['association'] + '\n') if 'association' in self.__lines else ''
        text += (self.__lines['location'] + '\n') if 'location' in self.__lines else ''
        text += (self.__lines['title'] + '\n') if 'title' in self.__lines else ''
        text += (self.__lines['method_details'] + '\n') if 'method_details' in self.__lines else ''
        text += (self.__lines['date'] + '\n') if 'date' in self.__lines else ''
        text += '\n'
        text += (self.__lines['ringers'] + '\n') if 'ringers' in self.__lines else ''
        if 'footnotes' in self.__lines:
            text += (self.__lines['footnotes'])
            text += '\n'
        text += (f'Linked event: {self.__lines["event"]}\n') if 'event' in self.__lines else ''
        text += (f'Bellboard: {get_url_from_id(self.__lines["id"])} ({self.__lines["bb_metadata"]})\n') \
            if 'bb_metadata' in self.__lines else ''
        text += (f'External reference: {self.__lines["external_reference"]}\n') if 'external_reference' in self.__lines else ''
        return text.strip()
