from pypeal.bellboard.interface import request_bytes
from pypeal.cli.chooser import choose_option
from pypeal.cli.prompts import confirm, panel, warning
from pypeal.entities.peal import Peal
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel


def prompt_commit_peal(peal: Peal) -> Peal:

    user_confirmed = False
    existing_peal = None
    if peal.bellboard_id and (existing_peal := Peal.get(bellboard_id=peal.bellboard_id)):
        warning(f'Peal with BellBoard ID {peal.bellboard_id} already exists:\n\n{existing_peal}')
        if not confirm(None, confirm_message='Overwrite peal?', default=False):
            return None
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
                warning('Possible duplicate peal')
                console = Console()
                console.print(Columns([Panel(str(dup)), Panel(str(peal))], width=80))
                diffs = ''
                for field, (left, right) in dup.diff(peal).items():
                    diffs += f'{field}: {left} -> {right}\n'
                panel(diffs.strip(), title='Differences')
                if confirm(None, confirm_message='Is this the same peal?'):
                    match choose_option(['Pick left', 'Pick right', 'Cancel'], default=1):
                        case 1:
                            existing_peal = peal
                            peal = dup
                        case 2:
                            pass
                        case 3:
                            return None

    panel(str(peal), title='Confirm performance')

    if not user_confirmed and not confirm('Save this peal?'):
        return None

    if existing_peal:
        existing_peal.delete()
    peal.commit()

    for photo in peal.photos:
        print(f'Saving photo {photo[1]}...')
        _, photo_bytes = request_bytes(photo[1])
        peal.set_photo_bytes(photo[0], photo_bytes)

    print(f'Peal (ID {peal.id}) added')

    return peal
