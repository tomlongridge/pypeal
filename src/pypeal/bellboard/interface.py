from datetime import datetime, timedelta
import logging
import time

from requests import RequestException, Response, get as get_request
from requests.exceptions import ConnectionError
from pypeal.config import get_config

BELLBOARD_PEAL_ID_URL = '/view.php?id=%s'
BELLBOARD_PEAL_RANDOM_URL = '/view.php?random'
BELLBOARD_PEAL_SEARCH_URL = '/export.php?'

__logger = logging.getLogger('pypeal')
__last_call: datetime = None


class BellboardError(Exception):
    pass


def search_peals(name: str) -> str:
    __logger.info('Searching for peals by ringer name "{name}"')
    _, response_xml = request(get_config('bellboard', 'url') + BELLBOARD_PEAL_SEARCH_URL + f'ringer={name}',
                              headers={'Accept': 'application/xml'})
    return response_xml


def get_peal(id: int) -> tuple[int, str]:
    url = get_url_from_id(id)
    __logger.info(f'Getting peal at {url}')
    response = request(url)
    __logger.info(f'Retrieved peal at {response[0]}')
    return (get_id_from_url(response[0]), response[1])


def request(url: str, headers: dict[str, str] = None) -> tuple[str, str]:

    # Rate-limit requests to avoid affecting BellBoard service
    global __last_call
    rate_limit_secs = int(get_config('bellboard', 'rate_limit_secs') or 1)
    if __last_call and __last_call < datetime.now() - timedelta(seconds=-rate_limit_secs):
        __logger.info(f'Waiting {rate_limit_secs}s before making BellBoard request...')
        time.sleep(rate_limit_secs)
    __last_call = datetime.now()

    try:
        response: Response = get_request(url, headers=headers if headers else None)
        if response.status_code == 404:
            raise BellboardError(f'No such peal in Bellboard at {url}')
        return (response.url, response.text)
    except ConnectionError as e:
        raise BellboardError(f'Unable to connect to Bellboard at {url}') from e
    except RequestException as e:
        raise BellboardError(f'Error whilst connecting to Bellboard at {url}: {e}') from e


def get_url_from_id(id: int) -> str:
    return get_config('bellboard', 'url') + (BELLBOARD_PEAL_ID_URL % id if id else BELLBOARD_PEAL_RANDOM_URL)


def get_id_from_url(url: str) -> int:
    if url and url.startswith('http') and url.find('id=') != -1:
        return int(url.split('id=')[1].split('&')[0])
    else:
        return None
