from pypeal import utils
from pypeal.bellboard.interface import BellboardError
from pypeal.bellboard.utils import get_url_from_id
from pypeal.bellboard.submit import get_bb_fields_from_peal, submit
from pypeal.cli.prompt_deduplicate_peal import prompt_bellboard_duplicate
from pypeal.cli.prompts import ask_int, confirm, panel, error, prompt_any
from pypeal.entities.peal import Peal


def prompt_submit_unpublished_peals():
    for peal in Peal.get_all():
        if peal.bellboard_id is None:
            prompt_submit_peal(peal)


def prompt_submit_peal(peal: int | Peal = None):

    if peal is None:
        peal = Peal.get(id=ask_int('Peal ID', min=1, required=True))
    elif type(peal) is int:
        peal = Peal.get(id=peal)
    elif peal.id is None:
        raise ValueError('Peal must be saved to database before submitting to BellBoard')

    panel(str(peal))

    if peal.bellboard_id is not None:
        if not confirm(f'Peal already submitted to BellBoard by {peal.bellboard_submitter} on ' +
                       f'{utils.format_date_short(peal.bellboard_submitted_date)}: {get_url_from_id(peal.bellboard_id)}',
                       confirm_message='Are you sure you want to submit it?',
                       default=False):
            return

    if bb_data := prompt_bellboard_duplicate(peal):
        if confirm(None, confirm_message=f'Link existing peal to this BellBoard ID {bb_data[0]}?'):
            peal.update_bellboard_id(*bb_data)
        return

    peal_fields = get_bb_fields_from_peal(peal)
    if confirm(None, confirm_message='Edit fields before submitting?', default=False):
        peal_fields = prompt_any(peal_fields, prompt=None)

    if not confirm(None, confirm_message='Submit peal?', default=True):
        return

    print('Submitting peal to BellBoard...')
    try:
        bb_peal_id, submitter_name = submit(peal_fields)
        print(f'Success: {get_url_from_id(bb_peal_id)}')
        peal.update_bellboard_id(bb_peal_id, submitter_name, utils.get_now())
        print('Updated peal with BellBoard ID')
    except BellboardError as e:
        error(f'Unable to submit peal: {e}')
