from pypeal import utils
from pypeal.cli.prompts import confirm
from pypeal.peal import Peal
from pypeal.tower import Bell


def prompt_validate_tenor(peal: Peal):

    if peal.ring is None:
        return

    tenor: Bell = peal.tenor

    if tenor.weight != peal.tenor_weight:
        print(f'Tenor weight {utils.get_weight_str(peal.tenor_weight)} reported on Bellboard does not match ' +
              f'the weight of largest bell rung ({utils.get_weight_str(tenor.weight)}) on Dove')
        if confirm(None, confirm_message=f'Use Dove value ({utils.get_weight_str(tenor.weight)})?'):
            peal.tenor_weight = None

    if tenor.note != peal.tenor_note:
        print(f'Tenor note {peal.tenor_note} reported on Bellboard does not match ' +
              f'the note of largest bell rung ({tenor.note}) on Dove')
        if confirm(None, confirm_message=f'Use Dove value ({tenor.note})?'):
            peal.tenor_note = None
