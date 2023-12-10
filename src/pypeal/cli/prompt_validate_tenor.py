import re

from pypeal import utils
from pypeal.cli.prompts import ask_int, warning
from pypeal.peal import Peal
from pypeal.tower import Bell
from pypeal.utils import get_num_words, word_to_num


RING_POSITION_REGEX = \
    re.compile(r'.*(?P<location>front|back) (?P<stage>[0-9]+|' + '|'.join(get_num_words()) + ').*',
               re.IGNORECASE)


def _prompt_shift_band(peal: Peal, suggested_tenor: Bell, quick_mode: bool):

    if quick_mode and not suggested_tenor:
        quick_mode = False  # Force a prompt for this in quick mode

    new_tenor = ask_int('Confirm tenor bell',
                        default=suggested_tenor.role if suggested_tenor else peal.ring.tenor.role,
                        min=1,
                        max=peal.ring.tenor.role,
                        required=True) if not quick_mode else suggested_tenor.role

    if new_tenor != peal.tenor.role:

        peal_ringers = peal.ringers
        band_shift = new_tenor - peal.tenor.role
        print(f'Shifting band by {band_shift} bell{"s" if abs(band_shift) > 1 else ""}')
        ring_start = new_tenor - peal.num_bells
        peal.clear_ringers()
        for ringer in peal_ringers:
            new_bells = []
            for bell in ringer.bell_nums:
                new_bells.append(peal.ring.get_bell(ring_start + bell).id)
            peal.add_ringer(ringer.ringer, new_bells, ringer.bell_nums, ringer.is_conductor)


def prompt_validate_tenor(peal: Peal, quick_mode: bool):

    if peal.ring is None:
        return

    reported_tenor: Bell = peal.tenor
    suggested_tenor: Bell = None

    # Check for a footnote declaring position of the band
    match_ring_position = None
    if len(peal.ringers) > 0 and peal.ringers[-1].bell_nums is not None:

        for footnote in peal.footnotes:
            if match_ring_position := re.match(RING_POSITION_REGEX, footnote.text):
                location, stage = match_ring_position.groups()
                if stage.isnumeric():
                    stage = int(stage)
                else:
                    stage = word_to_num(stage)
                if location == 'front':
                    suggested_tenor = peal.ring.get_bell(peal.num_bells)
                else:
                    suggested_tenor = peal.ring.tenor

                if suggested_tenor is not None and suggested_tenor != reported_tenor:
                    warning(f'Footnote suggests ringing on the {location} {stage}, but the tenor entered is the {reported_tenor.role}')
                    _prompt_shift_band(peal, suggested_tenor, quick_mode)

                break

    # Check tenor weight on BellBoard vs the selected bells, but only if it hasn't been shifted already
    #  (trust the footnote over the recorded weight)
    if match_ring_position is None and reported_tenor and reported_tenor.weight != peal.tenor_weight:
        warning(f'Tenor weight {utils.get_weight_str(peal.tenor_weight)} reported on Bellboard does not match ' +
                f'the weight of largest bell rung ({utils.get_weight_str(reported_tenor.weight)}) on Dove')
        # Does the reported tenor weight match any bell in the ring?
        bell: Bell
        for bell in peal.ring.bells.values():
            if bell.weight == peal.tenor_weight:
                suggested_tenor = bell
                print(f'Suggested tenor, based on weight: {bell.role} ({utils.get_weight_str(bell.weight)})')
                break

        _prompt_shift_band(peal, suggested_tenor, quick_mode)

    # Clear tenor details as it's linked to a ring
    peal.tenor_weight = None
    peal.tenor_note = None
