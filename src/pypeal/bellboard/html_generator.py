from datetime import datetime
import re
from itertools import zip_longest

from bs4 import BeautifulSoup
from pypeal import config

from pypeal.bellboard.interface import BellboardError, get_peal
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.generator import PealGenerator
from pypeal.entities.peal import BellType

DATE_LINE_INFO_REGEX = re.compile(r'[A-Za-z]+,\s(?P<date>[0-9]+\s[A-Za-z0-9]+\s[0-9]+)(?:\s' +
                                  r'in\s(?P<duration>[A-Za-z0-9\s]+))?\s?(?:\((?P<tenor>.*)\))?$')
DURATION_REGEX = re.compile(r'^(?:(?P<hours>\d{1,2})[h])$|^(?:(?P<mins>\d+)[m]?)$|' +
                            r'^(?:(?:(?P<hours_2>\d{1,2})[h])\s(?:(?P<mins_2>(?:[0]?|[1-5]{1})[0-9])[m]?))$')
PHOTO_URL_REGEX = re.compile(r'/\.(?P<url>/uploads/\w+/\w+)\-\w+\.(?P<ext>jpg|jpeg|png)')
METADATA_SUBMITTED_REGEX = \
    re.compile(r'.*?[\s]*First submitted (?P<date>[\w\d\s,]+) at [0-9\:]+(?: by (?P<submitter>[\w\d\s]+))\.$',
               re.MULTILINE)
METADATA_UPDATED_REGEX = re.compile(r'.*?[\s]*Last updated (?P<date>[\w\d\s,]+) at [0-9\:]+\.$', re.MULTILINE)
METADATA_IMPORTED_REGEX = \
    re.compile(r'.*?[\s]*Imported from (?P<source>[\w\d\s]+) entry (?P<id>[\d]+)(?:\s+\(submitted by (?P<submitter>[\w\d\s]+)\))?.$',
               re.MULTILINE)

COMPOSER_AND_COMPOSITION_REGEX = re.compile(r'(?P<composer>[^\(]+)(?:\((?P<note>.*)\))?')
CONDUCTOR_REGEX = re.compile(r'(?P<name>[^\(]+)\s?\((?P<conductor>.*)\)')

class HTMLPealGenerator(PealGenerator):

    def __init__(self):
        self.__peal_id = None
        self.__html = None

    def download(self, peal_id: int = None) -> int:
        self.__peal_id, self.__html = get_peal(peal_id)
        return self.__peal_id

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
            listener.bell_type(BellType.HANDBELLS)
        else:
            listener.bell_type(BellType.TOWER)

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

        listener.location(address_dedication, place, county, None)

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
        composer_str = url_str = composition_note = None
        if len(element) > 0:
            composer_element = element[0].select('span.composer.persona')
            if len(composer_element) > 0:
                composer_str = composer_element[0].text.strip()
                if match := re.match(COMPOSER_AND_COMPOSITION_REGEX, composer_str):
                    composer_info = match.groupdict()
                    composer_str = composer_info['composer'].strip()
                    if 'note' in composer_info:
                        composition_note = composer_info['note']
            url_element = element[0].select('a')
            if len(url_element) > 0:
                url_str = config.get_config('bellboard', 'url') + url_element[0]['href']
            composition_name_element = element[0].select('span.compname')
            if len(composition_name_element) > 0:
                composition_note = composition_name_element[0].text.strip()
        # Don't set composer yet - in case it's declared in ringer list

        # Get ringers and their bells and add them to the ringers list
        ringer_names = []
        ringer_bells = []
        conductors = []
        for ringer, bells in zip_longest(soup.select('span.ringer.persona'),  soup.select('span.bell')):
            if not ringer.text.strip(' -'):  # Remove empty ringer entries (e.g. COVID gaps)
                continue
            ringer_name = ringer.text
            conductor_marker = None
            if ringer.next_sibling:
                conductor_marker = ringer.next_sibling.lower().strip(' ()\xa0')
            elif conductor_match := re.match(CONDUCTOR_REGEX, ringer.text):
                conductor_data = conductor_match.groupdict()
                ringer_name = conductor_data['name'].strip()
                conductor_marker = conductor_data['conductor'].lower()
            ringer_names.append(ringer_name)
            ringer_bells.append([int(bell) for bell in bells.text.strip().split('–')] if bells else None)
            conductors.append(conductor_marker is not None and \
                              (conductor_marker == 'c' or \
                               conductor_marker == 'c and c' or \
                               'cond' in conductor_marker or \
                               'conductor' in conductor_marker or \
                               'calling' in conductor_marker))
            if composer_str is None and \
                    conductor_marker and \
                    (conductor_marker == 'c and c' or \
                     'comp' in conductor_marker or \
                     'composer' in conductor_marker):
                composer_str = ringer_name

        # Set the composition details ahead of ringers
        listener.composition_details(composer_str, url_str, composition_note)

        # For non-contiguous peals, we can safely assume the submitter has entered the bell number in the ring
        # rather than in the peal. Check whether the bell labels go up sequencially and if not, use them as the
        # bells in ring label. We also need to generate the number in the peal to use if this is the case.
        total_bells = 0
        last_bell = 0
        is_contiguous = True
        bell_nums_in_peal = []
        for ringer in ringer_bells:
            for bell in ringer or []:
                is_contiguous = False if bell - last_bell != 1 else is_contiguous
                last_bell = bell
                total_bells += 1
            bell_nums_in_peal.append(list(range(total_bells, total_bells + len(ringer))) if ringer else None)

        # Loop over the ringers and their bell (or bells) and add them to the peal
        for full_name, bells, bell_nums, is_conductor in zip(ringer_names, ringer_bells, bell_nums_in_peal, conductors):
            listener.ringer(full_name,
                            bells if is_contiguous else bell_nums,
                            bells if not is_contiguous else None,
                            is_conductor,
                            total_bells)
        
        if not total_bells:
            total_bells = len(ringer_names)

        for footnote in soup.select('div.footnote'):
            text = footnote.text.strip()
            if len(text) > 0:
                listener.footnote(text)
        listener.footnote(None)

        element = soup.select('p.paragraphs.linked-events.section')
        if len(element) > 0:
            event_url = element[0].select('a')[0]['href']
            listener.event(config.get_config('bellboard', 'url') +
                           event_url[event_url.rfind('/'):])
        else:
            listener.event(None)

        element = soup.select('div.image')
        if len(element) > 0:
            photo_url = element[0].select('img')[0]['src']
            caption_element = element[0].select('p.caption')[0]
            credit_element = caption_element.select('i')
            if len(credit_element) > 0:
                credit = credit_element[0].text.strip()[len('Photo: ')+1:-1]
                credit_element[0].decompose()
            else:
                credit = None
            caption = caption_element.text.strip()
            if not (url_parts := re.match(PHOTO_URL_REGEX, photo_url)):
                raise BellboardError('Unexpected photo URL format: ', photo_url)
            url_info = url_parts.groupdict()
            listener.photo(config.get_config('bellboard', 'url') + url_info['url'] + '.' + url_info['ext'],
                           caption,
                           credit)
        else:
            listener.photo(None, None, None)

        submitter_info = submitter = submitted_date = updated_date = external_source = external_ref = None
        for element in soup.select('p.metadata'):
            if match := re.match(METADATA_SUBMITTED_REGEX, element.text.strip()):
                submitter_info = match.groupdict()
                submitter = submitter_info['submitter'] if 'submitter' in submitter_info else None
                submitted_date = datetime.date(datetime.strptime(submitter_info['date'], '%A, %d %B %Y'))
            if match := re.match(METADATA_UPDATED_REGEX, element.text.strip()):
                updated_info = match.groupdict()
                updated_date = datetime.date(datetime.strptime(updated_info['date'], '%A, %d %B %Y'))
            elif match := re.match(METADATA_IMPORTED_REGEX, element.text.strip()):
                submitter_info = match.groupdict()
                if submitter is None and 'submitter' in submitter_info:
                    submitter = submitter_info['submitter']
                external_source = submitter_info['source']
                external_ref = submitter_info['id']

        listener.bellboard_metadata(submitter, submitted_date, updated_date)
        if external_source:
            listener.external_reference(f'{external_source.strip()} ID: {external_ref}')

        listener.end_peal()
