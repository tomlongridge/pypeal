from datetime import datetime
from typing import Iterator
import xml.etree.ElementTree as ET

from pypeal.bellboard.interface import BellboardError, search as do_search
from pypeal.peal import BellType


XML_NAMESPACE = '{http://bb.ringingworld.co.uk/NS/performances#}'


class BellboardSearchNoResultFoundError(BellboardError):
    def __init__(self, url: str):
        super().__init__('No peals found matching search criteria')
        self.url = url


def search(ringer_name: str = None,
           date_from: datetime.date = None,
           date_to: datetime.date = None,
           tower_id: int = None,
           place: str = None,
           county: str = None,
           dedication: str = None,
           association: str = None,
           title: str = None,
           bell_type: BellType = None,
           order_by_submission_date: bool = True,
           order_descending: bool = True) -> Iterator[int]:

    criteria = {}
    if ringer_name:
        criteria['ringer'] = ringer_name
    if date_from:
        criteria['from'] = date_from
    if date_to:
        criteria['to'] = date_to
    if tower_id:
        criteria['dove_tower'] = tower_id
    if place:
        criteria['place'] = place
    if county:
        criteria['region'] = county
    if dedication:
        criteria['address'] = dedication
    if association:
        criteria['association'] = association
    if title:
        criteria['title'] = title
    match bell_type:
        case None:
            pass
        case BellType.TOWER:
            criteria['bells_type'] = 'tower'
        case BellType.HANDBELLS:
            criteria['bells_type'] = 'hand'
    if order_by_submission_date:
        criteria['order'] = 'newest'
    else:
        criteria['order'] = ''
    if not order_descending:
        criteria['order'] = '+reverse'

    yield from _perform_search(criteria)


def search_by_url(url: str) -> Iterator[int]:

    if '?' not in url or '&' not in url:
        raise ValueError(f'Invalid search URL: {url}')

    criteria = {}
    for param in url.split('?')[1].split('&'):
        param_parts = param.split('=')
        if len(param_parts) == 2 and param_parts[0] not in ['page', 'edit']:
            criteria[param_parts[0]] = param_parts[1]
    yield from _perform_search(criteria)


def _perform_search(criteria: dict[str, any]) -> Iterator[int]:

    if len(criteria) == 0 or (len(criteria) == 1 and 'date_to' in criteria):
        raise BellboardError('No search criteria provided - requires "Date to" and at least one other field')

    page = 0
    found_peals = True
    while found_peals:

        found_peals = False
        page += 1
        _, xml_response = do_search(criteria, page)
        tree = ET.fromstring(xml_response)

        for performance in tree.findall(f'./{XML_NAMESPACE}performance'):
            found_peals = True
            yield int(performance.attrib['href'].split('=')[1])
