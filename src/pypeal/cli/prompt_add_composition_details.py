from pypeal.cli.prompt_add_ringer import prompt_add_ringer_by_name_match, prompt_add_ringer_by_search, prompt_commit_ringer
from pypeal.cli.prompts import ask, confirm
from pypeal.peal import Peal
from pypeal.ringer import Ringer


def prompt_add_composition_details(name: str, url: str, peal: Peal, quick_mode: bool):

    composer, composer_description = _prompt_add_composer(name, quick_mode)

    if composer:
        prompt_commit_ringer(composer, name, peal, quick_mode)
        peal.composer = composer
    elif composer_description:
        peal.composer_description = composer_description

    if url or composer or composer_description:
        peal.composition_url = ask('Composition URL', default=url, required=False) if not quick_mode else url


def _prompt_add_composer(name: str, quick_mode: bool) -> (Ringer, str):

    matched_ringer: Ringer = prompt_add_ringer_by_name_match(name, 'Composer: ', quick_mode) if name else None
    if not matched_ringer:
        if name:
            print(f'Composer: Attempting to find "{name}"')
        elif quick_mode or confirm('No composer attributed'):
            return (None, None)

        while True:

            matched_ringer = prompt_add_ringer_by_search(name, 'Composer: ', True, quick_mode)
            if matched_ringer is not None:  # Allow None option and exit
                if matched_ringer.id is None:
                    matched_ringer.is_composer = True  # Not yet saved, just update the field
                    return (matched_ringer, None)
                elif not matched_ringer.is_composer:
                    if quick_mode or confirm(f'"{matched_ringer}" is not a composer - change to composer?', default=True):
                        matched_ringer.is_composer = True
                        matched_ringer.commit()  # Existing ringer - update the record now
                    else:
                        continue  # Try input again
            else:
                return (None, ask('Composer description (e.g. RW Diary)', required=False, default=name))
            return (matched_ringer, None)
