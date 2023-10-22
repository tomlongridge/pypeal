from datetime import datetime, timedelta
import logging
import time

from requests import RequestException, Response, get as get_request
from pypeal.config import get_config

BELLBOARD_PEAL_ID_URL = '/view.php?id=%s'
BELLBOARD_PEAL_RANDOM_URL = '/view.php?random'

__logger = logging.getLogger('pypeal')
__last_call: datetime = None


class BellboardError(Exception):
    pass


def request(url: str) -> tuple[str, str]:

    # Rate-limit requests to avoid affecting BellBoard service
    global __last_call
    rate_limit_secs = int(get_config('bellboard', 'rate_limit_secs') or 1)
    if __last_call and __last_call < datetime.now() - timedelta(seconds=-rate_limit_secs):
        __logger.info(f'Waiting {rate_limit_secs}s before making BellBoard request...')
        time.sleep(rate_limit_secs)
    __last_call = datetime.now()

    try:
        response: Response = get_request(url)
        response.raise_for_status()
        return (response.url, response.text)
    except RequestException as e:
        raise BellboardError(f'Unable to access {url}: {e}') from e


def get_url_from_id(id: int) -> str:
    return get_config('bellboard', 'url') + (BELLBOARD_PEAL_ID_URL % id if id else BELLBOARD_PEAL_RANDOM_URL)


def get_id_from_url(url: str) -> int:
    if url and url.startswith('http') and url.find('id=') != -1:
        return int(url.split('id=')[1].split('&')[0])
    else:
        return None
