from pypeal.bellboard.interface import request_bytes
from pypeal.cli.prompts import confirm, panel, warning
from pypeal.peal import Peal


def prompt_commit_peal(peal: Peal) -> (bool, int):

    panel(str(peal), title='New performance')

    user_confirmed = False
    existing_peal = None
    if peal.bellboard_id and (existing_peal := Peal.get(bellboard_id=peal.bellboard_id)):
        warning(f'Peal with BellBoard ID {peal.bellboard_id} already exists:\n\n{existing_peal}')
        if not confirm(None, confirm_message='Overwrite peal?', default=False):
            return False, None
        else:
            user_confirmed = True

    if possible_duplicates := Peal.search(date_from=peal.date,
                                          date_to=peal.date,
                                          tower_id=peal.ring.tower.id if peal.ring else None,
                                          place=peal.place if not peal.ring else None,
                                          county=peal.county if not peal.ring else None,
                                          dedication=peal.dedication if not peal.ring else None):

        for dup in possible_duplicates:
            if dup.bellboard_id != peal.bellboard_id:  # We've already identified matching IDs above
                warning(f'Possible duplicate peal:\n\n{dup}')
                if confirm(None, confirm_message='Is this the same peal?'):
                    if confirm(None, confirm_message='Update BellBoard reference (peal has been edited)?', default=False):
                        dup.update_bellboard_id(peal.bellboard_id)
                        return True, None
                    else:
                        return False, None

    if not user_confirmed and not confirm('Save this peal?'):
        return False, None

    removed_peal_id = None
    if existing_peal:
        removed_peal_id = existing_peal.id
        existing_peal.delete()
    peal.commit()

    for photo in peal.photos:
        print(f'Saving photo {photo[1]}...')
        _, photo_bytes = request_bytes(photo[1])
        peal.set_photo_bytes(photo[0], photo_bytes)

    print(f'Peal (ID {peal.id}) added')

    return True, removed_peal_id
