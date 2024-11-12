import re
from pypeal.cli.prompt_add_ringer import prompt_add_ringer_by_name_match, prompt_add_ringer_by_search, prompt_commit_ringer
from pypeal.cli.prompts import ask, confirm
from pypeal.entities.peal import Peal
from pypeal.entities.ringer import Ringer

COMPOSITION_NOTE_REGEX = re.compile(r'^anon\.?$|anonymous|^trad\.?$|traditional|(?:old )rw diary', re.IGNORECASE)


def prompt_add_composition_details(name: str, url: str, note: str, peal: Peal, quick_mode: bool):

    if note:
        peal.composition_note = note
    elif name and COMPOSITION_NOTE_REGEX.match(name):
        peal.composition_note = name
        name = None

    matched_ringer = None
    if name:
        matched_ringer: Ringer = prompt_add_ringer_by_name_match(name, 'Composer: ', quick_mode)
        if peal.composition_note is None and matched_ringer is None and name and \
                confirm(f'No composer found matching "{name}" exactly',
                        confirm_message='Add as composition note?',
                        default=True):
            peal.composition_note = name
            name = None

    while True:

        if not matched_ringer:
            if name:
                print(f'Composer: Attempting to find "{name}"')
            elif quick_mode or confirm('No composer attributed'):
                break
            if not (matched_ringer := prompt_add_ringer_by_search(name, 'Composer: ', True, quick_mode)):
                break  # Chosen to skip conductor

        if matched_ringer:
            if matched_ringer.id is None:
                matched_ringer.is_composer = True  # Not yet saved, just update the field
            elif not matched_ringer.is_composer:
                if quick_mode or confirm(f'"{matched_ringer}" is not a composer - change to composer?', default=True):
                    matched_ringer.is_composer = True
                    matched_ringer.commit()  # Existing ringer - update the record now
                else:
                    continue  # Try input again
            break

    if matched_ringer:
        prompt_commit_ringer(matched_ringer, name)
        peal.composer = matched_ringer

    if peal.composition_note is None and (not quick_mode or (not peal.composer and name)):
        composition_note = name if not peal.composer and name else None  # Only default to name if it didn't match a ringer
        peal.composition_note = ask('Composition note', default=composition_note, required=False)

    if url or name or peal.composer:
        peal.composition_url = ask('Composition URL', default=url, required=False) if not quick_mode else url
