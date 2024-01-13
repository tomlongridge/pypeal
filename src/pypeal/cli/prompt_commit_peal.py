from pypeal.bellboard.interface import get_url_from_id, request_bytes
from pypeal.cli.prompts import confirm, panel, warning
from pypeal.peal import Peal


def prompt_commit_peal(peal: Peal) -> bool:

    if existing_peal := Peal.search(date_from=peal.date,
                                    date_to=peal.date,
                                    tower_id=peal.ring.tower.id if peal.ring else None,
                                    place=peal.place if not peal.ring else None,
                                    county=peal.county if not peal.ring else None,
                                    dedication=peal.dedication if not peal.ring else None):

        warning(f'Possible duplicate peal:\n\n{existing_peal[0]}')
        if not confirm(None, confirm_message='Continue?'):
            return False

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
