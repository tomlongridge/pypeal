from pypeal.cli.prompts import error
from pypeal.cli.prompts import ask, choose_option, confirm, prompt_names
from pypeal.peal import Peal
from pypeal.ringer import Ringer
from pypeal.utils import get_bell_label, split_full_name


def prompt_add_ringer(name: str, bell_nums: list[int], is_conductor: bool, peal: Peal):

    matched_ringer: Ringer = None

    full_name_match = Ringer.get_by_full_name(name)
    match len(full_name_match):
        case 0:
            pass  # Allow to continue to name matching
        case 1:
            if confirm(f'{get_bell_label(bell_nums)}: "{name}" -> {full_name_match[0]}', default=True):
                matched_ringer = full_name_match[0]
        case _:
            print(f'{get_bell_label(bell_nums)}: {len(full_name_match)} existing ringers match "{name}"')
            matched_ringer = choose_option(
                [f'{r.name} ({r.id})' for r in full_name_match], values=full_name_match, cancel_option='None', return_option=True)

    last_name, given_names = split_full_name(name)

    while not matched_ringer:

        print(f'{get_bell_label(bell_nums)}: Attempting to find "{name}"')

        match choose_option(['Add as new ringer', 'Search alternatives'], default=1):
            case 1:
                matched_ringer = Ringer(*prompt_names(last_name, given_names))
            case 2:
                search_last_name, search_given_names = prompt_names(last_name, given_names)
                potential_ringers = Ringer.get_by_name(search_last_name, search_given_names)
                match len(potential_ringers):
                    case 0:
                        print(f'No existing ringers match (given name: "{search_given_names}", last name: "{search_last_name}")')
                    case 1:
                        if confirm(f'{get_bell_label(bell_nums)}: "{name}" -> {potential_ringers[0]}', default=True):
                            matched_ringer = potential_ringers[0]
                    case _:
                        print(f'{len(potential_ringers)} existing ringers match "{(search_given_names + " " + search_last_name).strip()}"')
                        matched_ringer = choose_option(potential_ringers, cancel_option='None', return_option=True)

    if matched_ringer.id is None:
        matched_ringer.commit()

    if len(full_name_match) == 0 and \
            f'{given_names} {last_name}' != matched_ringer.name and \
            confirm(f'Add "{given_names} {last_name}" as an alias?'):
        matched_ringer.add_alias(last_name, given_names)

    bells = []
    while bell_nums is not None and len(bells) < len(bell_nums):

        if peal.stage is not None and peal.ring is not None and peal.stage.num_bells == len(peal.ring.bells):
            # There is no choice of bells as the stage size matches the number of bells in the tower
            bells += bell_nums
        else:

            suggested_bells = []
            if len(peal.ringers) and peal.ringers[-1][2] is not None:
                last_bell: int = peal.ringers[-1][2][-1]
                for i in range(len(bell_nums)):
                    suggested_bells.append(last_bell + i + 1)
            else:
                suggested_bells = bell_nums
            for bell in ask('Bell number(s) in the tower', default=get_bell_label(suggested_bells)).split(','):
                bell_list = bell.split('-')
                if len(bell_list) == 1:
                    if bell.isnumeric() and validate_bell([int(bell)], peal):
                        bells.append(int(bell))
                        continue
                else:
                    if bell_list[0].isnumeric() and bell_list[1].isnumeric():
                        bell_range = list(range(int(bell_list[0]), int(bell_list[1]) + 1))
                        if validate_bell(bell_range, peal):
                            bells += bell_range
                            continue
                error(f'Invalid bell number, list or range: {bell}')
            if len(bells) > len(bell_nums):
                if not confirm(f'More bells ({len(bells)}) than expected ({len(bell_nums)}) for this ringer', default=False):
                    bells = []

    peal.add_ringer(matched_ringer, bell_nums, bells if len(bells) > 0 else None, is_conductor)


def validate_bell(bells: list[int], peal: Peal) -> bool:
    for bell in bells:
        if peal.ring is not None and len(peal.ring.bells) < bell:
            if not confirm(f'Bell number ({bell}) exceeds number of bells in the tower', default=False):
                return False
        for ringer, _, bells, _ in peal.ringers:
            if bell in bells:
                if not confirm(f'Bell {bell} already assigned to {ringer.name}', default=False):
                    return False
    return True
