import logging

from bs4 import BeautifulSoup

from pypeal.bellboard.interface import BellboardError, get_url_from_id, request

_logger = logging.getLogger('pypeal')


# XML feed doesn't currently contain the tower ID, so we have to parse the HTML for it
def get_tower_id_from_html(peal_id: int) -> int:
    _logger.debug('Getting tower ID from Bellboard HTML page for peal %d', peal_id)
    try:
        _, html = request(get_url_from_id(peal_id))
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.select('span.place')
        if len(element) > 0:
            if element[0].parent.name == 'a':
                return int(element[0].parent['href'].split('/')[-1])
    except BellboardError as e:
        _logger.exception('Error getting tower ID from Bellboard HTML page: %s', e)
    return None
