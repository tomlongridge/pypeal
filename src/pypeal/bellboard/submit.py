import re
from pypeal import utils
from pypeal.bellboard.interface import BellboardError, submit_peal
from pypeal.entities.peal import BellType, Peal, PealType

SUBMITTED_SUCCESS_REGEX = re.compile(r'<a href="view.php\?id=(?P<peal_id>[0-9]+)">Your performance</a> has been added to BellBoard.')
SUBMITTER_REGEX = re.compile(r'<div id="whoami">You are logged in as <b><a href="/preferences">(?P<submitter>.*?)</a></b></div>')


def submit(peal: Peal) -> tuple[int, str]:

    response_html = \
        submit_peal(date_rung=peal.date,
                    place=peal.place,
                    title=peal.title,
                    ringers=[(pr.ringer.name + (' (c)' if pr.is_conductor else ''), pr.bell_nums) for pr in peal.ringers],
                    is_general_ringing=peal.type == PealType.GENERAL_RINGING,
                    is_in_hand=peal.bell_type == BellType.HANDBELLS,
                    association=peal.association,
                    region_or_county=peal.county,
                    address_or_dedication=(peal.address if peal.address else peal.dedication) +
                                          (f', {peal.sub_place}' if peal.sub_place else ''),
                    changes=peal.changes,
                    duration=utils.get_time_str(peal.duration),
                    tenor_size=utils.get_weight_str(peal.ring.tenor.weight),
                    details=peal.composition_note,
                    composer=peal.composer,
                    footnotes=[str(footnote) for footnote in peal.footnotes])

    if match := SUBMITTED_SUCCESS_REGEX.search(response_html):
        bb_peal_id = int(match.group('peal_id'))
        if submitter_match := SUBMITTER_REGEX.search(response_html):
            submitter = submitter_match.group('submitter')
        else:
            submitter = None
        return bb_peal_id, submitter
    else:
        raise BellboardError('Unexpected peal submission response: ' + response_html)
