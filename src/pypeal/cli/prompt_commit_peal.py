from pypeal.bellboard.interface import get_url_from_id, request_bytes
from pypeal.cli.prompts import confirm, panel
from pypeal.peal import Peal


def prompt_commit_peal(peal: Peal) -> bool:

    panel(str(peal), title=get_url_from_id(peal.bellboard_id))
    if not confirm('Save this peal?'):
        return False

    peal.commit()
    print(f'Peal {peal.bellboard_id} added')

    for photo in peal.photos:
        print(f'Saving photo {photo[1]}...')
        _, photo_bytes = request_bytes(photo[1])
        peal.set_photo_bytes(photo[0], photo_bytes)

    return True
