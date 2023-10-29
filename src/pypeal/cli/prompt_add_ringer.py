from pypeal.cli.prompts import choose_option, confirm, prompt_names
from pypeal.peal import Peal
from pypeal.ringer import Ringer
from pypeal.utils import get_bell_label, split_full_name


def prompt_add_ringer(name: str, bells: list[int], is_conductor: bool, peal: Peal):

    matched_ringer: Ringer = None

    full_name_match = Ringer.get_by_full_name(name)
    match len(full_name_match):
        case 0:
            pass  # Allow to continue to name matching
        case 1:
            if confirm(f'{get_bell_label(bells)}: "{name}" -> {full_name_match[0]}', default=True):
                matched_ringer = full_name_match[0]
        case _:
            print(f'{get_bell_label(bells)}: {len(full_name_match)} existing ringers match "{name}"')
            matched_ringer = choose_option(
                [f'{r.name} ({r.id})' for r in full_name_match], values=full_name_match, cancel_option='None', return_option=True)

    while not matched_ringer:

        print(f'{get_bell_label(bells)}: Attempting to find "{name}"')

        last_name, given_names = split_full_name(name)

        match choose_option(['Add as new ringer', 'Search alternatives'], default=1):
            case 1:
                if (ringer_names := prompt_names(last_name, given_names)):
                    matched_ringer = Ringer(*ringer_names)
            case 2:
                if not (ringer_names := prompt_names(last_name, given_names)):
                    break
                last_name, given_names = ringer_names
                potential_ringers = Ringer.get_by_name(last_name, given_names)
                match len(potential_ringers):
                    case 0:
                        print(f'No existing ringers match (given name: "{given_names}", last name: "{last_name}")')
                    case 1:
                        if confirm(f'{get_bell_label(bells)}: "{name}" -> {potential_ringers[0]}', default=True):
                            matched_ringer = potential_ringers[0]
                    case _:
                        print(f'{len(potential_ringers)} existing ringers match "{(given_names + " " + last_name).strip()}"')
                        matched_ringer = choose_option(potential_ringers, cancel_option='None', return_option=True)

    if matched_ringer.id is None:
        matched_ringer.commit()

    if len(full_name_match) == 0 and \
            f'{given_names} {last_name}' != matched_ringer.name and \
            confirm(f'Add "{given_names} {last_name}" as an alias?'):
        matched_ringer.add_alias(last_name, given_names)

    peal.add_ringer(matched_ringer, bells, is_conductor)
