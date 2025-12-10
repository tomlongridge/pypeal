from pypeal import utils
from pypeal.bellboard.interface import BellboardError, get_bb_fields_from_peal, login as bellboard_login
from pypeal.bellboard.preview import get_preview
from pypeal.bellboard.utils import get_url_from_id
from pypeal.bellboard.submit import BellboardDuplicateError, submit, submit_bulk
from pypeal.cli.prompt_deduplicate_peal import prompt_bellboard_duplicate, prompt_peal_diff
from pypeal.cli.prompts import ask_int, confirm, heading, panel, error, prompt_any
from pypeal.entities.peal import Peal


def prompt_submit_unpublished_peals(in_bulk: bool = False):
    try:
        if in_bulk is True or (in_bulk is None and confirm(None, confirm_message='Submit all peals in bulk?', default=False)):
            prompt_bulk_upload(list(filter(lambda p: p.bellboard_id is None, Peal.get_all())))
        else:
            for peal in Peal.get_all():
                if peal.bellboard_id is None:
                    prompt_submit_peal(peal)
                    if not confirm(None, confirm_message='Continue to next peal?'):
                        break
    except BellboardError as e:
        error(e)


def prompt_submit_peal(peal: int | Peal = None):

    heading('Submit/update peal to BellBoard')

    if peal is None:
        peal = Peal.get(id=ask_int('Peal ID', min=1, required=True))
    elif type(peal) is int:
        peal = Peal.get(id=peal)
    elif peal.id is None:
        raise ValueError('Peal must be saved to database before submitting to BellBoard')

    submit_peal(peal)


def submit_peal(peal: Peal):

    if peal.bellboard_id is None:
        if bb_data := prompt_bellboard_duplicate(peal):
            if Peal.get(bellboard_id=bb_data[0]):
                error(f'Peal with BellBoard ID {bb_data[0]} already exists in database')
            elif confirm(None, confirm_message=f'Link existing peal to this BellBoard ID {bb_data[0]}?'):
                peal.update_bellboard_id(*bb_data)
            return
    elif prompt_peal_diff(peal.bellboard_id, peal, 'Database', 'Update?') is None:
        return

    bellboard_login()

    peal_fields = get_bb_fields_from_peal(peal)
    panel(peal_fields_to_str(peal_fields), title='New Peal Details' if peal.bellboard_id is None else 'Updated Peal Details')

    if confirm(None, confirm_message='Edit fields before submitting?', default=False):
        peal_fields = prompt_any(peal_fields,
                                 prompt=None,
                                 required_fields=['place', 'region', 'date_rung', 'title', 'ringers', 'perf_type', 'bells_type'])

    if not confirm(None, confirm_message='Submit peal?', default=True):
        return

    print('Sending details to BellBoard...')
    try:
        bb_peal_id, submitter_name = submit(peal_fields, peal.bellboard_id)
        panel(f'Success: {get_url_from_id(bb_peal_id)}')
        peal.update_bellboard_id(bb_peal_id, submitter_name, utils.get_now())
        print(f'Updated peal {peal.id} with BellBoard ID {bb_peal_id}')
    except BellboardError as e:
        error(f'Unable to submit peal: {e}')


def prompt_bulk_upload(peals: list[Peal]):

    heading('Submit bulk peals to BellBoard')

    for peal in peals:

        # Check for a duplicate on BellBoard ourselves
        if bb_data := prompt_bellboard_duplicate(peal):
            if confirm(None, confirm_message=f'Link existing peal to this BellBoard ID {bb_data[0]}?'):
                peal.update_bellboard_id(*bb_data)
                continue

        force_upload = False
        while True:
            # Attempt to submit to BellBoard API and update peal with response ID
            # (parsing the submitted peal to get submitter details for our database)
            try:
                bellboard_id = submit_bulk(peal, force_upload)
                bb_data = get_preview(bellboard_id)
                peal.update_bellboard_id(*bb_data)

            except BellboardDuplicateError as e:
                # If BellBoard API reports a duplicate, prompt user to link to existing peal
                if bb_data := prompt_bellboard_duplicate(peal, e.duplicate_ids):
                    if confirm(None, confirm_message=f'Link existing peal to this BellBoard ID {bb_data[0]}?'):
                        peal.update_bellboard_id(*bb_data)

                # Otherwise push the peal up anyway, if we don't think it's a duplicate
                if confirm(None, confirm_message='Force upload the peal?', default=False):
                    force_upload = True
                    continue

            except BellboardError as e:
                error(f'Unable to submit peal: {e}')
                if confirm(None, confirm_message='Retry upload?', default=False):
                    continue

            break


def peal_fields_to_str(peal_fields: dict) -> str:
    response = ''
    for k, v in peal_fields.items():
        if v and k == 'ringers':
            response += 'Ringers:\n'
            for ringer in v:
                response += f' - {ringer["bell_1"]}'
                response += f', {ringer["bell_2"]}' if ringer['bell_2'] else ''
                response += ' ' + ringer['text'] + '\n'
        elif v and k == 'footnotes':
            response += f'Footnotes:\n{v}\n'
        else:
            response += f'{k.title().replace("_", " ")}: {v}\n'
    return response.strip()
