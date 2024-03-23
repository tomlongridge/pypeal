from pypeal import utils
from pypeal.bellboard.interface import BellboardError, get_url_from_id
from pypeal.bellboard.submit import submit
from pypeal.cli.prompts import ask_int, confirm, panel, error
from pypeal.entities.peal import Peal


def prompt_submit_peal(peal: int | Peal = None):

    if peal is None:
        peal = Peal.get(id=ask_int('Peal ID', min=1, required=True))
    elif type(peal) is int:
        peal = Peal.get(id=peal)
    elif peal.id is None:
        raise ValueError('Peal must be saved to database before submitting to BellBoard')

    panel(str(peal))

    if peal.bellboard_id is None:
        if not confirm(None, confirm_message='Submit peal?', default=True):
            return
    else:
        if not confirm(f'Peal already submitted to BellBoard by {peal.bellboard_submitter} on ' +
                       f'{utils.format_date_short(peal.bellboard_submitted_date)}: {get_url_from_id(peal.bellboard_id)}',
                       confirm_message='Are you sure you want to submit it?',
                       default=False):
            return

    # for bb_peal_id, _ in find_matching_peal(peal):
    #     panel(str(bb_peal), title='Matching peal on BellBoard')
    #     if not confirm(None, confirm_message='Submit this peal instead?', default=False):
    #         return

    print('Submitting peal to BellBoard...')
    try:
        bb_peal_id, submitter_name = submit(peal)
        print(f'Success: {get_url_from_id(bb_peal_id)}')
        peal.update_bellboard_id(bb_peal_id, submitter_name, utils.get_now())
        print('Updated peal with BellBoard ID')
    except BellboardError as e:
        error(f'Unable to submit peal: {e}')
