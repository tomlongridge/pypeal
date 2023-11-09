from datetime import datetime
import re

from bs4 import BeautifulSoup
from pypeal import config

from pypeal.bellboard.interface import BellboardError, get_peal
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.peal import BellType

DATE_LINE_INFO_REGEX = re.compile(r'[A-Za-z]+,\s(?P<date>[0-9]+\s[A-Za-z0-9]+\s[0-9]+)(?:\s' +
                                  r'in\s(?P<duration>[A-Za-z0-9\s]+))?\s?(?:\((?P<tenor>.*)\))?$')
DURATION_REGEX = re.compile(r'^(?:(?P<hours>\d{1,2})[h])$|^(?:(?P<mins>\d+)[m]?)$|' +
                            r'^(?:(?:(?P<hours_2>\d{1,2})[h])\s(?:(?P<mins_2>(?:[0]?|[1-5]{1})[0-9])[m]?))$')


class HTMLPealGenerator():

    def __init__(self):
        self.__peal_id = None
        self.__html = None

    def download(self, peal_id: int = None):
        self.__peal_id, self.__html = get_peal(peal_id)

    def parse(self, listener: PealGeneratorListener):

        listener.new_peal(self.__peal_id)

        soup = BeautifulSoup(self.__html, 'html.parser')

        element = soup.select('div.association')
        if len(element) > 0:
            listener.association(element[0].text.strip())
        else:
            listener.association(None)

        element = soup.select('div.ringers.two-in-hand.handbells')
        if len(element) > 0:
            listener.type(BellType.HANDBELLS)
        else:
            listener.type(BellType.TOWER)

        place = None
        county = None
        address_dedication = None

        element = soup.select('span.place')
        if len(element) > 0:
            if element[0].parent.name == 'a':
                listener.tower(dove_id=int(element[0].parent['href'].split('/')[-1]))
            place = element[0].text.strip()
            if element[0].next_sibling:
                county = element[0].next_sibling.text.strip(', ')

        element = soup.select('div.address')
        if len(element) > 0:
            address_dedication = element[0].text.strip()

        listener.location(address_dedication, place, county)

        element = soup.select('span.changes')
        if len(element) > 0:
            listener.changes(int(element[0].text.strip()))
        else:
            listener.changes(None)

        element = soup.select('span.title')
        if len(element) > 0:
            title = element[0].text.strip()
            if element[0].next_sibling:
                title += f' {element[0].next_sibling.text.strip()}'
            listener.title(title)
        else:
            raise BellboardError(f'Unable to find title in peal {id}')

        element = soup.select('div.details')
        if len(element) > 0:
            listener.method_details(element[0].text.strip())
        else:
            listener.method_details(None)

        element = soup.select('div.attribution')
        composer_str = url_str = None
        if len(element) > 0:
            composer_element = element[0].select('span.composer.persona')
            if len(composer_element) > 0:
                composer_str = composer_element[0].text.strip()
            url_element = element[0].select('a')
            if len(url_element) > 0:
                url_str = config.get_config('bellboard', 'url') + url_element[0]['href']
        listener.composer(composer_str,  url_str)

        # The date line is the first line of the performance div that doesn't have a class
        for peal_detail in soup.select('div.performance')[0].children:
            if not peal_detail.attrs or 'class' not in peal_detail.attrs:
                date_line = peal_detail.text.strip()
                if not (date_line_match := re.match(DATE_LINE_INFO_REGEX, date_line)):
                    raise BellboardError(f'Unable to parse date line: {date_line}')

                date_line_info = date_line_match.groupdict()
                listener.date(datetime.date(datetime.strptime(date_line_info['date'], '%d %B %Y')))
                listener.tenor(date_line_info['tenor'])
                listener.duration(date_line_info['duration'])
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
            listener.ringer(full_name, bells, is_conductor)

        found_footnote: bool = False
        for footnote in soup.select('div.footnote'):
            text = footnote.text.strip()
            if len(text) > 0:
                listener.footnote(text)
                found_footnote = True
        if not found_footnote:
            listener.footnote(None)

        element = soup.select('p.paragraphs.linked-events.section')
        if len(element) > 0:
            event_url = element[0].select('a')[0]['href']
            listener.event(config.get_config('bellboard', 'url') +
                           event_url[event_url.rfind('/'):])
        else:
            listener.event(None)

        listener.end_peal()
