from datetime import datetime, timedelta, date
import logging
import time

from requests import RequestException, Response, get as get_request
from requests.exceptions import ConnectionError
import urllib.parse
from pypeal.config import get_config

BELLBOARD_PEAL_ID_URL = '/view.php?id=%s'
BELLBOARD_PEAL_RANDOM_URL = '/view.php?random'
BELLBOARD_PEAL_SEARCH_URL = '/search.php?'

__logger = logging.getLogger('pypeal')
__last_call: datetime = None


class BellboardError(Exception):
    pass


def search(criteria: dict[str, any] = None, page: int = 1) -> [str, str]:
    query_str = ''
    for key, value in criteria.items():
        if type(value) in [datetime, date]:
            value = urllib.parse.quote(value.strftime("%d/%m/%Y"))
        query_str += f'&{key}={value}'

    url = get_config('bellboard', 'url') + BELLBOARD_PEAL_SEARCH_URL + f'page={page}{query_str}'
    __logger.info(f'Searching peals on Bellboard: {url}')
    _, response_xml = request(url, headers={'Accept': 'application/xml'})
    return url, response_xml


def get_peal(id: int) -> tuple[int, str]:
    url = get_url_from_id(id)
    __logger.info(f'Getting peal at {url}')
    response = request(url)
    __logger.info(f'Retrieved peal at {response[0]}')
    return (get_id_from_url(response[0]), response[1])


def _request(url: str, headers: dict[str, str] = None) -> Response:

    # Rate-limit requests to avoid affecting BellBoard service
    global __last_call
    rate_limit_secs = int(get_config('bellboard', 'rate_limit_secs') or 1)
    if __last_call and __last_call < datetime.now() - timedelta(seconds=-rate_limit_secs):
        __logger.info(f'Waiting {rate_limit_secs}s before making BellBoard request...')
        time.sleep(rate_limit_secs)
    __last_call = datetime.now()

    try:
        __logger.debug(f'GET request to {url}')
        response: Response = get_request(url, headers=headers if headers else None)
        if response.status_code == 404:
            raise BellboardError(f'No such file in Bellboard at {url}')
        return response
    except ConnectionError as e:
        raise BellboardError(f'Unable to connect to Bellboard at {url}') from e
    except RequestException as e:
        raise BellboardError(f'Error whilst connecting to Bellboard at {url}: {e}') from e


def request(url: str, headers: dict[str, str] = None) -> tuple[str, str]:
    response = _request(url, headers=headers)
    return (response.url, response.text)


def request_bytes(url: str, headers: dict[str, str] = None) -> tuple[str, bytes]:
    response = _request(url, headers=headers)
    return (response.url, response.content)


def get_url_from_id(id: int) -> str:
    return get_config('bellboard', 'url') + (BELLBOARD_PEAL_ID_URL % id if id else BELLBOARD_PEAL_RANDOM_URL)


def get_id_from_url(url: str) -> int:
    if url and url.startswith('http') and url.find('id=') != -1:
        return int(url.split('id=')[1].split('&')[0])
    else:
        return None
