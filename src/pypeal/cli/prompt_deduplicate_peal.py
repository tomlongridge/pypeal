from datetime import date
from pypeal.bellboard.html_generator import HTMLPealGenerator
from pypeal.bellboard.interface import BellboardError
from pypeal.bellboard.utils import get_url_from_id
from pypeal.cli.peal_previewer import PealPreviewListener
from pypeal.cli.prompts import confirm, warning
from pypeal.entities.peal import Peal
from pypeal.bellboard.search import find_matching_peal


# Check database and BellBoard for similar peals and return either the Peal entity or a BellBoard ID (if it's not in the database yet)
# If None is returned then the user has confirmed there is no duplicate
def prompt_get_duplicate_peal(peal: Peal | int) -> Peal | int:

    # Check for existing peal with the same BellBoard ID
    if type(peal) is int:
        bellboard_id = peal
    elif peal.bellboard_id:
        bellboard_id = peal.bellboard_id

    if bellboard_id and (existing_peal := Peal.get(bellboard_id=bellboard_id)):
        warning(f'Peal with BellBoard ID {bellboard_id} already exists in database:\n\n{existing_peal}')
        return existing_peal

    # Check for existing peal with the same basic details
    if existing_peals := Peal.search(date_from=peal.date or None,
                                     date_to=peal.date or None,
                                     tower_id=peal.ring.tower.id if peal.ring else None,
                                     place=peal.place or None,
                                     county=peal.county or None,
                                     dedication=peal.dedication or None,
                                     association=peal.association or None,
                                     bell_type=peal.bell_type or None,
                                     length_type=peal.length_type or None):
        warning(f'{len(existing_peals)} possible duplicate peals found in database')
        for existing_peal in existing_peals:
            warning(str(existing_peal))
            if confirm(None, confirm_message='Is this the same peal?'):
                return existing_peal

    return prompt_check_bellboard_duplicate(peal)


def prompt_check_bellboard_duplicate(peal: Peal) -> tuple[int, str, date]:

    # Check BellBoard for peal with the same basic details
    generator = HTMLPealGenerator()
    preview_listener = PealPreviewListener()
    first_peal = True
    for bb_peal_id, search_url in find_matching_peal(peal):
        if first_peal:
            warning(f'Possible duplicate peals found on BellBoard: {search_url}')
            if not confirm(None, confirm_message='Check these peals for duplicates?'):
                return None

        try:
            peal_id = generator.download(bb_peal_id)
            generator.parse(preview_listener)
            warning(preview_listener.text, title=get_url_from_id(peal_id))
            if confirm(None, confirm_message='Is this the same peal?'):
                return bb_peal_id, *preview_listener.metadata
        except BellboardError as e:
            warning(f'[Unable to get peal preview: {e}]', title=get_url_from_id(peal_id))

        first_peal = False

    return None
