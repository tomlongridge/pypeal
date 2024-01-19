from pypeal.bellboard.interface import get_url_from_id, request_bytes
from pypeal.cli.prompts import confirm, panel, warning
from pypeal.peal import Peal


def prompt_commit_peal(peal: Peal) -> (bool, int):

    if possible_duplicates := Peal.search(date_from=peal.date,
                                          date_to=peal.date,
                                          tower_id=peal.ring.tower.id if peal.ring else None,
                                          place=peal.place if not peal.ring else None,
                                          county=peal.county if not peal.ring else None,
                                          dedication=peal.dedication if not peal.ring else None):

        for dup in possible_duplicates:
            if dup.bellboard_id != peal.bellboard_id:
                warning(f'Possible duplicate peal:\n\n{dup}')
                if not confirm(None, confirm_message='Continue?'):
                    return False, None

    panel(str(peal), title=get_url_from_id(peal.bellboard_id))

    removed_peal_id = None
    if peal.bellboard_id and (existing_peal := Peal.get(bellboard_id=peal.bellboard_id)):
        warning(f'Peal {peal.bellboard_id} already exists')
        if confirm(None, confirm_message='Overwrite peal?', default=False):
            removed_peal_id = existing_peal.id
            existing_peal.delete()
        else:
            return False, None
    elif not confirm('Save this peal?'):
        return False, None

    peal.commit()
    print(f'Peal (ID {peal.id}) added')

    for photo in peal.photos:
        print(f'Saving photo {photo[1]}...')
        _, photo_bytes = request_bytes(photo[1])
        peal.set_photo_bytes(photo[0], photo_bytes)

    return True, removed_peal_id
