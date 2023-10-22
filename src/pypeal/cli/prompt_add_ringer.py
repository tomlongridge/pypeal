from pypeal.cli.prompts import ask, choose_option, confirm
from pypeal.peal import Peal
from pypeal.ringer import Ringer


def prompt_add_ringer(name: str, bells: list[int], is_conductor: bool, peal: Peal):

    # Holds the ringer record that matches the name found on Bellboard
    matched_ringer: Ringer = None

    full_name_match = Ringer.get_by_full_name(name)
    match len(full_name_match):
        case 0:
            pass  # Allow to continue to name matching
        case 1:
            matched_ringer = confirm_add_ringer(name, full_name_match[0], bells)
        case _:
            print(f'{get_bell_label(bells)}: {len(full_name_match)} existing ringers match "{name}"')
            matched_ringer = choose_option(
                [f'{r.name} ({r.id})' for r in full_name_match], values=full_name_match, cancel_option='None', return_option=True)

    while not matched_ringer:

        print(f'{get_bell_label(bells)}: No existing ringers match "{name}"')

        last_name, given_names = split_full_name(name)

        match choose_option(['Add as new ringer', 'Search alternatives'], default=1, cancel_option='Cancel'):
            case 1:
                if (ringer_names := prompt_ringer_names(last_name, given_names)):
                    matched_ringer = Ringer(*ringer_names)
            case 2:
                if not (ringer_names := prompt_ringer_names(last_name, given_names)):
                    break
                last_name, given_names = ringer_names
                potential_ringers = Ringer.get_by_name(last_name, given_names)
                match len(potential_ringers):
                    case 0:
                        print(f'No existing ringers match (given name: "{given_names}", last name: "{last_name}")')
                    case 1:
                        matched_ringer = confirm_add_ringer(name, potential_ringers[0], bells)
                    case _:
                        print(f'{len(potential_ringers)} existing ringers match "{(given_names + " " + last_name).strip()}"')
                        matched_ringer = choose_option(potential_ringers, cancel_option='None', return_option=True)
            case None:
                return None

    if matched_ringer.id is None:
        matched_ringer.commit()

    if len(full_name_match) == 0 and \
            f'{given_names} {last_name}' != matched_ringer.name and \
            confirm(f'Add "{given_names} {last_name}" as an alias?'):
        matched_ringer.add_alias(last_name, given_names)

    peal.add_ringer(matched_ringer, bells, is_conductor)


def get_bell_label(bells: list[int]) -> str:
    return ",".join([str(bell) for bell in bells])


def confirm_add_ringer(name: str, ringer: Ringer, bells: list[int]) -> Ringer:
    if confirm(f'{get_bell_label(bells)}: "{name}" -> {ringer}',
               confirm_message='Is this the correct ringer?',
               default=True):
        return ringer
    return None


def prompt_ringer_names(default_last_name: str = None, default_given_names: str = None) -> tuple[str, str]:
    if (last_name := ask('Last name', default=default_last_name)) and \
       (given_names := ask('Given name(s)', default=default_given_names)):
        return last_name, given_names
    return None


def split_full_name(full_name: str) -> tuple[str, str]:
    last_name = full_name.split(' ')[-1]
    given_names = ' '.join(full_name.split(' ')[:-1])
    return last_name, given_names
