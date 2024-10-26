import re

from requests import Response
from pypeal.bellboard.interface import BellboardError, get_bb_fields_from_peal, submit_peal, submit_peal_xml
from pypeal.entities.peal import Peal

SUBMITTED_SUCCESS_REGEX = re.compile(r'<a href="view.php\?id=(?P<peal_id>[0-9]+)">Your performance</a> has been added to BellBoard.')
SUBMITTER_REGEX = re.compile(r'<div id="whoami">You are logged in as <b><a href="/preferences">(?P<submitter>.*?)</a></b></div>')


class BellboardDuplicateError(BellboardError):
    def __init__(self, duplicate_ids: list[int]):
        self.duplicate_ids = duplicate_ids
        super().__init__(f'Duplicate peals detected on BellBoard: {duplicate_ids}')


def submit(peal: Peal | dict) -> tuple[int, str]:

    if type(peal) is Peal:
        params = get_bb_fields_from_peal(peal)
    else:
        params = peal

    response_html = submit_peal(params)

    if match := SUBMITTED_SUCCESS_REGEX.search(response_html):
        bb_peal_id = int(match.group('peal_id'))
        if submitter_match := SUBMITTER_REGEX.search(response_html):
            submitter = submitter_match.group('submitter')
        else:
            submitter = None
        return bb_peal_id, submitter
    else:
        raise BellboardError('Unexpected peal submission response: ' + response_html)


def submit_bulk(peals: list[Peal], force: bool = False) -> int:

    response: Response = submit_peal_xml(peals, force)

    match response.status_code:
        case 200:
            return int(response.text.split())
        case 409:
            raise BellboardDuplicateError(response.text.split())
        case 500:
            raise BellboardError(f'Internal server error from BellBoard: {response.text}')
        case _:
            raise BellboardError(f'Unexpected response f{response.status_code} from BellBoard: {response.text}')
