import re
from pypeal.cli.prompts import warning
from pypeal.peal import Peal
from pypeal.utils import get_num_words, word_to_num


RING_POSITION_REGEX = \
    re.compile(r'.*(?P<location>front|back) (?P<stage>[0-9]+|' + '|'.join(get_num_words()) + ').*',
               re.IGNORECASE)


def prompt_validate_footnotes(peal: Peal, quick_mode: bool):

    if peal.ring is None or len(peal.ringers) == 0 or peal.ringers[-1][1] is None:
        return

    for footnote in peal.footnotes:
        if match := re.match(RING_POSITION_REGEX, footnote[0]):
            location, stage = match.groups()
            if stage.isnumeric():
                stage = int(stage)
            else:
                stage = word_to_num(stage)
            suggested_tenor = peal.ring.get_tenor(bells_rung=peal.num_bells,
                                                  from_front=location == 'front')
            actual_tenor = peal.ringers[-1][1][-1]
            if suggested_tenor != actual_tenor:
                warning(f'Footnote suggests ringing on the {location} {stage}, but the tenor entered is the {actual_tenor}')
        break
