from pypeal.cli.prompts import ask_int, error

from pypeal.entities.peal import Peal, PealType


def prompt_add_changes(changes_input: str, peal: Peal, quick_mode: bool):

    changes = None
    while True:

        if changes_input:
            try:
                changes = int(changes_input)
                if changes < 0 or changes > 100_000:
                    error(f'Invalid duration: {changes_input}')
                    changes = None
            except ValueError:
                error(f'Invalid duration: {changes_input}')

        if (changes is None and peal.type != PealType.GENERAL_RINGING) or not quick_mode:
            changes = ask_int('Number of changes', default=changes, required=False, min=1, max=100_000)

        if changes is None and peal.type != PealType.GENERAL_RINGING:
            error('Number of changes is required unless this is general ringing')
        else:
            peal.changes = changes
            return
