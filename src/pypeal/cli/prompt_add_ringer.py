from pypeal.cli.prompts import error
from pypeal.cli.prompts import ask, choose_option, confirm, prompt_names
from pypeal.peal import Peal
from pypeal.ringer import Ringer
from pypeal.utils import get_bell_label, split_full_name


def prompt_add_ringer(name: str, bell_nums: list[int], is_conductor: bool, peal: Peal, quick_mode: bool):

    matched_ringer: Ringer = prompt_add_ringer_by_full_name_match(name, get_bell_label(bell_nums), quick_mode)

    while not matched_ringer:
        if not quick_mode:
            print(f'{get_bell_label(bell_nums)}: Attempting to find "{name}"')
            matched_ringer = prompt_add_ringer_by_search(name, get_bell_label(bell_nums), quick_mode)

    prompt_commit_ringer(matched_ringer, name, peal, quick_mode)

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
            bell_nums_str = get_bell_label(suggested_bells)
            if quick_mode:
                if bell_nums[0] == 1:
                    bell_nums_str = ask('First bell number(s) in the tower', default=bell_nums_str)
                else:
                    pass  # Use the default for subsequent bells in quick mode
            else:
                bell_nums_str = ask('Bell number(s) in the tower', default=bell_nums_str)
            for bell in bell_nums_str.split(','):
                bell_list = bell.split('-')
                if len(bell_list) == 1:
                    if bell.isnumeric() and _validate_bell([int(bell)], peal):
                        bells.append(int(bell))
                        continue
                else:
                    if bell_list[0].isnumeric() and bell_list[1].isnumeric():
                        bell_range = list(range(int(bell_list[0]), int(bell_list[1]) + 1))
                        if _validate_bell(bell_range, peal):
                            bells += bell_range
                            continue
                error(f'Invalid bell number, list or range: {bell}')
                bells = []
                quick_mode = False
                break
            if len(bells) > len(bell_nums):
                if not confirm(f'More bells ({len(bells)}) than expected ({len(bell_nums)}) for this ringer', default=False):
                    bells = []
                    quick_mode = False

    peal.add_ringer(matched_ringer, bell_nums, bells if len(bells) > 0 else None, is_conductor)


def prompt_add_ringer_by_search(name: str, label: str, quick_mode: bool) -> Ringer:

    last_name, given_names = split_full_name(name)
    while True:
        match choose_option(['Add new ringer', 'Search ringers'], default=1) if not quick_mode else 1:
            case 1:
                if not quick_mode or \
                        confirm(f'"{name}" not found in database' if name else None, confirm_message='Add new ringer?', default=True):
                    return Ringer(*prompt_names(last_name, given_names))
                else:
                    quick_mode = False
                    continue
            case 2:
                quick_mode = False
                search_last_name, search_given_names = prompt_names(last_name, given_names)
                potential_ringers = Ringer.get_by_name(search_last_name, search_given_names)
                match len(potential_ringers):
                    case 0:
                        print(f'No existing ringers match (given name: "{search_given_names}", last name: "{search_last_name}")')
                        continue
                    case 1:
                        if confirm(f'{label}: "{name}" -> {potential_ringers[0]}', default=True):
                            return potential_ringers[0]
                    case _:
                        print(f'{len(potential_ringers)} existing ringers match "{(search_given_names + " " + search_last_name).strip()}"')
                        return choose_option(potential_ringers, cancel_option='None', return_option=True)


def prompt_add_ringer_by_full_name_match(name: str, label: str, quick_mode: bool) -> Ringer:

    if name is None:
        return None

    full_name_match = Ringer.get_by_full_name(name)
    match len(full_name_match):
        case 0:
            return None
        case 1:
            if quick_mode or confirm(f'{label}: "{name}" -> {full_name_match[0]}', default=True):
                return full_name_match[0]
        case _:
            print(f'{label}: {len(full_name_match)} existing ringers match "{name}"')
            if quick_mode:
                return full_name_match[0]
            else:
                return choose_option([f'{r.name} ({r.id})' for r in full_name_match],
                                     values=full_name_match,
                                     cancel_option='None',
                                     return_option=True)


def prompt_commit_ringer(ringer: Ringer, used_name: str, peal: Peal, quick_mode: bool):
    if ringer.id is None:
        ringer.commit()

    last_name, given_names = split_full_name(used_name)
    if used_name != ringer.name and \
            len(ringer.get_aliases(last_name=last_name, given_names=given_names)) == 0 and \
            (quick_mode or confirm(None, confirm_message='Add an alias for this ringer?')):
        ringer.add_alias(last_name,
                         given_names,
                         is_primary=choose_option([used_name, ringer.name], prompt='Which name should be displayed?') == 1)


def _validate_bell(bells: list[int], peal: Peal) -> bool:
    for bell in bells:
        if peal.ring is not None and len(peal.ring.bells) < bell:
            if not confirm(f'Bell number ({bell}) exceeds number of bells in the tower', default=False):
                return False
        for ringer, _, bells, _ in peal.ringers:
            if bell in bells:
                if not confirm(f'Bell {bell} already assigned to {ringer.name}', default=False):
                    return False
    return True
