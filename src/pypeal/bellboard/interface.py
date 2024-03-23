from datetime import datetime, timedelta, date
import logging
import time

import requests
from requests import RequestException, Response
from requests.sessions import Session
from requests.exceptions import ConnectionError
import urllib.parse
from pypeal import utils
from pypeal.config import get_config

BELLBOARD_PEAL_ID_URL = '/view.php?id=%s'
BELLBOARD_PEAL_RANDOM_URL = '/view.php?random'
BELLBOARD_PEAL_SEARCH_URL = '/search.php?'


__logger = logging.getLogger('pypeal')
__last_call: datetime = None
__session: Session = None


class BellboardError(Exception):
    pass


def search(criteria: dict[str, any] = None, page: int = 1) -> tuple[str, str]:
    url = get_search_url(criteria) + f'&page={page}'
    __logger.info(f'Searching peals on Bellboard: {url}')
    _, response_xml = request(url, headers={'Accept': 'application/xml'})
    return url, response_xml


def get_search_url(criteria: dict[str, any] = None) -> str:
    query_str = ''
    for key, value in criteria.items():
        if type(value) in [datetime, date]:
            value = urllib.parse.quote(value.strftime("%d/%m/%Y"))
        query_str += f'&{key}={value}'

    url = get_config('bellboard', 'url') + BELLBOARD_PEAL_SEARCH_URL + query_str.strip('&')
    return url


def login() -> Session:
    url = get_config('bellboard', 'url') + '/login.php'
    __logger.info(f'Logging in to Bellboard at {url}')
    payload = {
        'email': get_config('bellboard', 'username'),
        'password': get_config('bellboard', 'password'),
        'forever': '1',
        'login': 'Login'
    }
    session = requests.session()
    response = _request(url, payload=payload, session=session)
    if response.status_code == 200:
        return session
    else:
        raise BellboardError(f'Unable to login to Bellboard as {payload["email"]}: {response.status_code}')


def submit_peal(date_rung: datetime.date,
                place: str,
                title: str,
                ringers: list[tuple[str, list[int]]],
                is_general_ringing: bool = False,
                is_in_hand: bool = False,
                association: str = None,
                region_or_county: str = None,
                address_or_dedication: str = None,
                changes: int = None,
                duration: str = None,
                tenor_size: str = None,
                details: str = None,
                composer: str = None,
                footnotes: list[str] = None) -> str:

    global __session
    if __session is None:
        __session = login()

    if changes is None and \
       'rounds' not in title.lower() and \
       'call changes' not in title.lower() and \
       'tolling' not in title.lower() and \
       'firing' not in title.lower() and \
       'general ringing' not in title.lower():
        raise BellboardError('Changes must be specified for peals that are not rounds, call changes, tolling, firing or general ringing')

    payload = {
        'date_rung': date_rung.strftime("%d/%m/%Y"),
        'bells_type': 'hand' if is_in_hand else 'tower',
        'perf_type': 'general_ringing' if is_general_ringing else 'assigned_bells',
        'association': association,
        'place': place,
        'region': region_or_county,
        'address': address_or_dedication,
        'changes': str(changes),
        'title': title,
        'duration': duration,
        'tenor_size': tenor_size,
        'details': details,
        'composer': composer,
        'footnotes': '\n'.join(footnotes) if footnotes else None,
        'submit': 'Submit'
    }

    for ringer, bells in ringers:
        if len(bells) == 1:
            payload[f'ringers[{bells[0]}]'] = ringer
        elif len(bells) == 2:
            payload[f'ringers[{bells[0]}-{bells[1]}]'] = ringer
        else:
            raise BellboardError(f'Unable to submit peal for ringer with {len(bells)} bells: {ringer}')

    url = get_config('bellboard', 'url') + '/submit.php'
    __logger.info(f'Submitting peal to Bellboard at {url}')

    return _request(url, payload=payload, session=__session).text


def get_peal(id: int) -> tuple[int, str]:
    url = get_url_from_id(id)
    __logger.info(f'Getting peal at {url}')
    response = request(url)
    __logger.info(f'Retrieved peal at {response[0]}')
    return (get_id_from_url(response[0]), response[1])


def _request(url: str, payload: dict = None, headers: dict[str, str] = None, session: Session = None) -> Response:

    # Rate-limit requests to avoid affecting BellBoard service
    global __last_call
    rate_limit_secs = int(get_config('bellboard', 'rate_limit_secs') or 1)
    if __last_call and __last_call < utils.get_now() - timedelta(seconds=-rate_limit_secs):
        __logger.info(f'Waiting {rate_limit_secs}s before making BellBoard request...')
        time.sleep(rate_limit_secs)
    __last_call = utils.get_now()

    try:
        response: Response
        if payload is None:
            __logger.debug(f'GET request to {url}')
            if session:
                response = session.get(url, headers=headers if headers else None)
            else:
                response = requests.get(url, headers=headers if headers else None)
        else:
            __logger.debug(f'POST request to {url} with payload: {payload}')
            if session:
                response = session.post(url, data=payload, headers=headers if headers else None)
            else:
                response = requests.post(url, data=payload, headers=headers if headers else None)
        if response.status_code == 404:
            raise BellboardError(f'No such page in Bellboard at {url}')
        return response
    except ConnectionError as e:
        raise BellboardError(f'Unable to connect to Bellboard at {url}') from e
    except RequestException as e:
        raise BellboardError(f'Error whilst connecting to Bellboard at {url}: {e}') from e


def request(url: str, payload: dict = None, headers: dict[str, str] = None) -> tuple[str, str]:
    response = _request(url, payload=payload, headers=headers)
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
