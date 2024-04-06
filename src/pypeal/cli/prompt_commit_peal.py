from pypeal.bellboard.interface import request_bytes
from pypeal.cli.chooser import choose_option
from pypeal.cli.prompt_deduplicate_peal import prompt_database_duplicate
from pypeal.cli.prompts import confirm, panel
from pypeal.entities.peal import Peal


def prompt_commit_peal(peal: Peal) -> Peal:

    user_confirmed = False
    existing_peal = None
    if duplicate_peal := prompt_database_duplicate(peal):
        match choose_option(['Keep existing', 'Use new', 'Cancel'], default=1):
            case 1:
                # Forget about the new peal but update the BellBoard ID to the new one
                # (Bellboard creates new IDs when a peal as been edited)
                duplicate_peal.update_bellboard_id(peal.bellboard_id, peal.bellboard_submitter, peal.bellboard_submitted_date)
                peal = None
            case 2:
                # Delete the existing peal and commit the new one
                existing_peal = duplicate_peal
                user_confirmed = True
            case 3:
                return None

    if peal:

        panel(str(peal), title='Confirm performance')
        if not user_confirmed and not confirm('Save this peal?'):
            return None

        # Clear the old BellBoard ID to avoid key clash
        if existing_peal:
            existing_peal.update_bellboard_id(None)

        peal.commit()
        for photo in peal.photos:
            print(f'Saving photo {photo[1]}...')
            _, photo_bytes = request_bytes(photo[1])
            peal.set_photo_bytes(photo[0], photo_bytes)

        print(f'Peal (ID {peal.id}) added')

    if existing_peal:
        print(f'Removing previous performance (ID {existing_peal.id})...')
        existing_peal.delete()

    return peal
