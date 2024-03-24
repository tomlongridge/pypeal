import re
from pypeal.bellboard.interface import BellboardError, get_bb_fields_from_peal, submit_peal
from pypeal.entities.peal import Peal

SUBMITTED_SUCCESS_REGEX = re.compile(r'<a href="view.php\?id=(?P<peal_id>[0-9]+)">Your performance</a> has been added to BellBoard.')
SUBMITTER_REGEX = re.compile(r'<div id="whoami">You are logged in as <b><a href="/preferences">(?P<submitter>.*?)</a></b></div>')


def submit(peal: Peal | dict) -> tuple[int, str]:

    if type(peal) is Peal:
        params = get_bb_fields_from_peal(peal)
    else:
        params = peal

    response_html = submit_peal(**params)

    if match := SUBMITTED_SUCCESS_REGEX.search(response_html):
        bb_peal_id = int(match.group('peal_id'))
        if submitter_match := SUBMITTER_REGEX.search(response_html):
            submitter = submitter_match.group('submitter')
        else:
            submitter = None
        return bb_peal_id, submitter
    else:
        raise BellboardError('Unexpected peal submission response: ' + response_html)
