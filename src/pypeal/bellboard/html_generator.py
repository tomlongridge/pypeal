from datetime import datetime
import re

from bs4 import BeautifulSoup

from pypeal.bellboard.interface import BellboardError, get_peal
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.peal import Peal, PealType

DATE_LINE_INFO_REGEX = re.compile(r'[A-Za-z]+,\s(?P<date>[0-9]+\s[A-Za-z0-9]+\s[0-9]+)(?:\s' +
                                  r'in\s(?P<duration>[A-Za-z0-9\s]+))?\s?(?:\((?P<tenor>.*)\))?$')
DURATION_REGEX = re.compile(r'^(?:(?P<hours>\d{1,2})[h])$|^(?:(?P<mins>\d+)[m]?)$|' +
                            r'^(?:(?:(?P<hours_2>\d{1,2})[h])\s(?:(?P<mins_2>(?:[0]?|[1-5]{1})[0-9])[m]?))$')


class HTMLPealGenerator():

    def __init__(self, listener: PealGeneratorListener):
        self.__listener = listener

    def get(self, peal_id: int = None) -> Peal:
        return self.get_peal_from_html(*get_peal(peal_id))

    def get_peal_from_html(self, id: int, html: str) -> Peal:

        self.__listener.new_peal(id)

        soup = BeautifulSoup(html, 'html.parser')

        element = soup.select('div.association')
        if len(element) > 0:
            self.__listener.association(element[0].text.strip())
        else:
            self.__listener.association(None)

        element = soup.select('div.ringers.two-in-hand.handbells')
        if len(element) > 0:
            self.__listener.type(PealType.HANDBELLS)
        else:
            self.__listener.type(PealType.TOWER)

        place = None
        county = None
        address_dedication = None

        element = soup.select('span.place')
        if len(element) > 0:
            if element[0].parent.name == 'a':
                self.__listener.tower(dove_id=int(element[0].parent['href'].split('/')[-1]))
            place = element[0].text.strip()
            if element[0].next_sibling:
                county = element[0].next_sibling.text.strip(', ')

        element = soup.select('div.address')
        if len(element) > 0:
            address_dedication = element[0].text.strip()

        self.__listener.location(address_dedication, place, county)

        element = soup.select('span.changes')
        if len(element) > 0:
            self.__listener.changes(int(element[0].text.strip()))
        else:
            self.__listener.changes(None)

        element = soup.select('span.title')
        if len(element) > 0:
            title = element[0].text.strip()
            if element[0].next_sibling:
                title += f' {element[0].next_sibling.text.strip()}'
            self.__listener.title(title)
        else:
            raise BellboardError(f'Unable to find title in peal {id}')

        element = soup.select('div.details')
        if len(element) > 0:
            self.__listener.method_details(element[0].text.strip())
        else:
            self.__listener.method_details(None)

        element = soup.select('span.composer.persona')
        if len(element) > 0:
            self.__listener.composer(element[0].text.strip())
        else:
            self.__listener.composer(None)

        # The date line is the first line of the performance div that doesn't have a class
        for peal_detail in soup.select('div.performance')[0].children:
            if not peal_detail.attrs or 'class' not in peal_detail.attrs:
                self.__parse_date_line(peal_detail.text.strip())
                break

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
            self.__listener.ringer(full_name, bells, is_conductor)

        found_footnote: bool = False
        for footnote in soup.select('div.footnote'):
            text = footnote.text.strip()
            if len(text) > 0:
                self.__listener.footnote(text)
                found_footnote = True
        if not found_footnote:
            self.__listener.footnote(None)

        return self.__listener.peal

    def __parse_date_line(self, date_line: str):

        if not (date_line_match := re.match(DATE_LINE_INFO_REGEX, date_line)):
            raise BellboardError(f'Unable to parse date line: {date_line}')

        date_line_info = date_line_match.groupdict()
        self.__listener.date(datetime.strptime(date_line_info['date'], '%d %B %Y'))
        self.__listener.tenor(date_line_info['tenor'])
        self.__listener.duration(date_line_info['duration'])
