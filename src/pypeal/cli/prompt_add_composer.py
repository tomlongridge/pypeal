from pypeal.cli.prompts import ask, choose_option, confirm, prompt_names
from pypeal.peal import Peal
from pypeal.ringer import Ringer
from pypeal.utils import split_full_name


def prompt_add_composer(name: str, url: str, peal: Peal, quick_mode: bool):

    matched_ringer: Ringer = None

    if name:
        full_name_match = Ringer.get_by_full_name(name)
        match len(full_name_match):
            case 0:
                pass  # Allow to continue to name matching
            case 1:
                if quick_mode or confirm(f'Composer: "{name}" -> {full_name_match[0]}', default=True):
                    matched_ringer = full_name_match[0]
            case _:
                print(f'Composer: {len(full_name_match)} existing ringers match "{name}"')
                if quick_mode:
                    matched_ringer = full_name_match[0]
                else:
                    matched_ringer = choose_option([f'{r.name} ({r.id})' for r in full_name_match],
                                                   values=full_name_match,
                                                   cancel_option='None',
                                                   return_option=True)

    if not matched_ringer:
        if name:
            print(f'Composer: Attempting to find "{name}"')
            last_name, given_names = split_full_name(name)
        else:
            if quick_mode or confirm('No composer attributed'):
                return
            last_name, given_names = None, None

    while not matched_ringer:

        match choose_option(['Add as new ringer', 'Search alternatives'], default=1) if not quick_mode else 1:
            case 1:
                if not quick_mode or \
                        confirm(f'"{name}" not found in database', confirm_message='Add as new ringer?', default=True):
                    matched_ringer = Ringer(*prompt_names(last_name, given_names), True)
                else:
                    quick_mode = False
                    continue
            case 2:
                quick_mode = False
                search_last_name, search_given_names = prompt_names(last_name, given_names)
                potential_ringers = Ringer.get_by_name(search_last_name, search_given_names)
                match len(potential_ringers):
                    case 0:
                        print(f'No existing ringers match (given name: "{search_last_name}", last name: "{search_last_name}")')
                    case 1:
                        if confirm(f'Composer: {potential_ringers[0]}', default=True):
                            matched_ringer = potential_ringers[0]
                    case _:
                        print(f'{len(potential_ringers)} existing ringers match "{(search_last_name + " " + search_last_name).strip()}"')
                        matched_ringer = choose_option(potential_ringers, cancel_option='None', return_option=True)

    if not matched_ringer.is_composer:
        if quick_mode or confirm(f'"{matched_ringer}" is not a composer - change to composer?', default=True):
            matched_ringer.is_composer = True
            matched_ringer.commit()
        else:
            matched_ringer = None

    if matched_ringer.id is None:
        matched_ringer.commit()

    if len(full_name_match) == 0 and \
            name != matched_ringer.name and \
            (quick_mode or confirm(f'Add "{name}" as an alias?')):
        matched_ringer.add_alias(last_name, given_names)

    peal.composer = matched_ringer
    peal.composition_url = ask('Composition URL', default=url, required=False) if not quick_mode else url
