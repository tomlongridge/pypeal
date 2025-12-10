from datetime import datetime, timedelta, date
import logging
import time
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
import requests
from requests import RequestException, Response
from requests.sessions import Session
from requests.exceptions import ConnectionError
import urllib.parse
from pypeal import utils
from pypeal.bellboard.consts import BELLBOARD_PEAL_SEARCH_URL
from pypeal.bellboard.utils import get_id_from_url, get_url_from_id
from pypeal.config import get_config
from pypeal.entities.peal import BellType, Peal, PealType


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

    global __session
    if __session:
        return __session

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
    if response.status_code != 200:
        raise BellboardError(f'Unable to login to Bellboard as {payload["email"]}: {response.status_code}')

    response_html = BeautifulSoup(response.content, 'html.parser')
    if login_detail := response_html.find('div', id='whoami'):
        if login_detail.select('a'):
            logged_in_as_name = login_detail.select('a')[0].text
            __logger.info(f'Logged in to Bellboard as: {logged_in_as_name}')
            __session = session
            return session
    elif response_html.select("p.error"):
        raise BellboardError(f'Unable to login to Bellboard as {payload["email"]}: {response_html.select("p.error")[0].text}')

    raise BellboardError(f'Unable to login to Bellboard as {payload["email"]}: unable to parse response')


def submit_peal(fields: dict[str, str], id: int = None) -> Response:

    if fields['changes'] is None and \
       'rounds' not in fields['title'].lower() and \
       'call changes' not in fields['title'].lower() and \
       'tolling' not in fields['title'].lower() and \
       'firing' not in fields['title'].lower() and \
       'general ringing' not in fields['title'].lower():
        raise BellboardError('Changes must be specified for peals that are not rounds, call changes, tolling, firing or general ringing')

    payload = {
        **fields,
        'submit': 'Submit'
    }

    bell_count = 1
    for ringer in fields['ringers']:
        if 'bell_2' in ringer and ringer['bell_2'] is not None:
            payload[f'ringers[{ringer["bell_1"]}-{ringer["bell_2"]}]'] = ringer['text']
            bell_count += 2
        elif 'bell_1' in ringer and ringer['bell_1'] is not None:
            payload[f'ringers[{ringer["bell_1"]}]'] = ringer['text']
            bell_count += 1
        else:
            payload[f'ringers[{bell_count}]'] = ringer['text']
            bell_count += 1
    del payload['ringers']

    url = get_config('bellboard', 'url')
    if id is not None:
        url += f'/edit.php?id={id}'
        __logger.info(f'Updating peal in Bellboard at {url}')
    else:
        url += '/submit.php'
        __logger.info(f'Submitting peal to Bellboard at {url}')

    return _request(url, payload=payload).text


def submit_peal_xml(peal: Peal, force: bool = False) -> Response:

    performance = ET.Element('performance', xmlns='http://bb.ringingworld.co.uk/NS/performances#')

    if peal.association:
        ET.SubElement(performance, 'association').text = peal.association
    place = ET.SubElement(performance, 'place')
    if peal.ring:
        place.attrib['dove-tower-id'] = str(peal.ring.tower.dove_id)
    ET.SubElement(place, 'place-name', type='place').text = peal.place
    dedication_str = ''
    if peal.dedication:
        dedication_str += peal.dedication
    elif peal.address:
        dedication_str += peal.address
    if peal.sub_place:
        dedication_str += f', {peal.sub_place}'
    ET.SubElement(place, 'place-name', type='dedication').text = dedication_str.strip(', ')
    ET.SubElement(place, 'place-name', type='county').text = peal.ring.tower.county

    ET.SubElement(place, 'ring', type='hand' if peal.bell_type == BellType.HANDBELLS else 'tower', tenor=peal.tenor_description)
    ET.SubElement(performance, 'date').text = peal.date.strftime('%Y-%m-%d')
    if peal.duration:
        ET.SubElement(performance, 'duration').text = utils.get_time_str(peal.duration)
    title = ET.SubElement(performance, 'title')
    if peal.changes:
        ET.SubElement(title, 'changes').text = str(peal.changes)
    ET.SubElement(title, 'method').text = peal.title
    details_str = ''
    if peal.methods:
        details_str += peal.get_method_summary()
    if peal.composition_note:
        details_str += peal.composition_note
    if len(details_str):
        ET.SubElement(title, 'details').text = details_str
    if peal.composer:
        ET.SubElement(title, 'composer', role='composed').text = peal.composer.name
    ringers = ET.SubElement(performance, 'ringers')
    for peal_ringer in peal.ringers:
        ringer = ET.SubElement(ringers, 'ringer')
        ringer.text = peal_ringer.ringer.get_name(peal.date)
        if peal_ringer.bell_nums:
            if len(peal_ringer.bell_nums) == 1:
                ringer.attrib['bell'] = str(peal_ringer.bell_nums[0])
            else:
                ringer.attrib['bells'] = f'{peal_ringer.bell_nums[0]}-{peal_ringer.bell_nums[-1]}'
        if peal_ringer.is_conductor:
            ringer.attrib['conductor'] = 'true'
    for footnote in peal.get_footnote_summary().split('\n'):
        ET.SubElement(performance, 'footnote').text = footnote

    payload = ET.tostring(performance, encoding='utf-8', method='xml').decode()

    url = get_config('bellboard', 'url') + '/import.php'  # 'old' is used to avoid peals showing in Latest page
    if force:
        url += '&force'
    __logger.info(f'Submitting peal to Bellboard at {url}')

    return _request(url, payload=payload, headers={'Content-Type': 'application/xml'})


def get_bb_fields_from_peal(peal: Peal) -> dict:
    ringer_data = []
    for ringer in peal.ringers:
        ringer_data.append({
            'bell_1': str(ringer.bell_nums[0]) if ringer.bell_nums and len(ringer.bell_nums) > 0 else None,
            'bell_2': str(ringer.bell_nums[1]) if ringer.bell_nums and len(ringer.bell_nums) > 1 else None,
            'text': ringer.ringer.get_name(peal.date) + (' (c)' if ringer.is_conductor else '')
        })

    details_str = ''
    if peal.methods:
        details_str += peal.get_method_summary()
    details_str += '\n'
    if peal.composition_note:
        details_str += peal.composition_note
    details_str = details_str.strip()

    return {
        'association': peal.association,
        'place': peal.place,
        'region': peal.county,
        'address': (peal.address if peal.address else peal.dedication) +
                   (f', {peal.sub_place}' if peal.sub_place else ''),
        'date_rung': peal.date.strftime("%d/%m/%Y"),
        'duration': utils.get_time_str(peal.duration) if peal.duration else None,
        'tenor_size': peal.tenor_description,
        'changes': str(peal.changes),
        'title': peal.title,
        'details': details_str if len(details_str) else None,
        'composer': peal.composer,
        'ringers': ringer_data,
        'footnotes': peal.get_footnote_summary() if peal.footnotes else None,
        'perf_type': 'general_ringing' if peal.type == PealType.GENERAL_RINGING else 'assigned_bells',
        'bells_type': 'hand' if peal.bell_type == BellType.HANDBELLS else 'tower',
    }


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

    if session is None:
        global __session
        if __session is None:
            __session = login()
        session = __session

    if get_config('bellboard', 'basicauth_username'):
        basic_auth = get_config('bellboard', 'basicauth_username'), \
                     get_config('bellboard', 'basicauth_password')
    else:
        basic_auth = None

    try:
        response: Response
        if payload is None:
            __logger.debug(f'GET request to {url}')
            response = session.get(url, headers=headers if headers else None, auth=basic_auth)
        else:
            __logger.debug(f'POST request to {url} with payload: {payload}')
            response = session.post(url, data=payload, headers=headers if headers else None, auth=basic_auth)
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
