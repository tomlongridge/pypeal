import logging
from pypeal.cli.prompts import error, warning
from pypeal.cli.prompts import ask, confirm
from pypeal.cli.chooser import choose_option
from pypeal.peal import Peal
from pypeal.ringer import Ringer
from pypeal.utils import get_bell_label
from pypeal.parsers import parse_ringer_name


_logger = logging.getLogger('pypeal')


def prompt_add_ringer(name: str,
                      bell_nums_in_peal: list[int],
                      bell_nums_in_ring: list[int],
                      is_conductor: bool,
                      peal: Peal,
                      quick_mode: bool):

    if peal.stage is not None:
        max_possible_bells = peal.stage.value + (1 if peal.stage.value % 2 == 1 else 0)
        if bell_nums_in_peal[-1] > max_possible_bells:
            warning(f'Bell number ({bell_nums_in_peal[-1]}) exceeds expected number of bells in the peal ({max_possible_bells}), ' +
                    'based on method(s)')
            if not confirm(None, default=False):
                return

    if bell_nums_in_ring and peal.ring and bell_nums_in_ring[-1] > peal.ring.num_bells:
        warning(f'Bell role ({bell_nums_in_ring[-1]}) exceeds number of bells in the tower ({peal.ring.num_bells}) - ignoring')
        bells = None

    bell_label = get_bell_label(bell_nums_in_peal) + ': ' if bell_nums_in_peal else ''

    matched_ringer: Ringer = prompt_add_ringer_by_name_match(name, bell_label, quick_mode)

    while not matched_ringer:
        print(f'{get_bell_label(bell_nums_in_peal) or "Ringer"}: Couldn\'t find ringer matching "{name}" (or aliases)')
        matched_ringer = prompt_add_ringer_by_search(name, bell_label, False, quick_mode)

    prompt_commit_ringer(matched_ringer, name, peal, quick_mode)

    if bell_nums_in_ring is not None \
       and not quick_mode \
       and not confirm(f'Use bell(s) {get_bell_label(bell_nums_in_ring)} for {name}?', default=True):
        bell_nums_in_ring = None

    if bell_nums_in_ring is None:

        bell_nums_in_ring = []
        while bell_nums_in_peal is not None and len(bell_nums_in_ring) < len(bell_nums_in_peal):

            if peal.stage is not None and peal.ring is not None and peal.stage.num_bells == len(peal.ring.bells):
                # There is no choice of bells as the stage size matches the number of bells in the tower
                bell_nums_in_ring += bell_nums_in_peal
            else:

                suggested_bells = []
                if len(peal.ringers) and peal.ringers[-1].bell_ids is not None:
                    last_bell_id: int = peal.ringers[-1].bell_ids[-1]
                    last_bell = peal.ring.get_bell_by_id(last_bell_id).role
                    for i in range(len(bell_nums_in_peal)):
                        suggested_bells.append(last_bell + i + 1)
                else:
                    suggested_bells = bell_nums_in_peal
                bell_nums_str = get_bell_label(suggested_bells)
                if quick_mode:
                    if bell_nums_in_peal[0] == 1:
                        bell_nums_str = ask('First bell number(s) in the tower', default=bell_nums_str)
                    else:
                        pass  # Use the default for subsequent bells in quick mode
                else:
                    bell_nums_str = ask('Bell number(s) in the tower', default=bell_nums_str)
                for bell in bell_nums_str.split(','):
                    bell_list = bell.split('-')
                    if len(bell_list) == 1:
                        if bell.isnumeric() and _validate_bell(bell_nums_in_peal, [int(bell)], peal):
                            bell_nums_in_ring.append(int(bell))
                            continue
                    else:
                        if bell_list[0].isnumeric() and bell_list[1].isnumeric():
                            bell_range = list(range(int(bell_list[0]), int(bell_list[1]) + 1))
                            if _validate_bell(bell_nums_in_peal, bell_range, peal):
                                bell_nums_in_ring += bell_range
                                continue
                    error(f'Invalid bell number, list or range: {bell}')
                    bell_nums_in_ring = []
                    quick_mode = False
                    break
                if len(bell_nums_in_ring) > len(bell_nums_in_peal):
                    if not confirm(f'More bells ({len(bells)}) than expected ({len(bell_nums_in_peal)}) for this ringer', default=False):
                        bell_nums_in_ring = []
                        quick_mode = False

    if peal.ring and len(bell_nums_in_ring) > 0:
        bell_ids = [peal.ring.bells[bell].id for bell in bell_nums_in_ring]
    else:
        bell_ids = None
    peal.add_ringer(matched_ringer, bell_ids, bell_nums_in_peal, is_conductor)


def prompt_add_ringer_by_search(name: str, label: str, allow_none: bool, quick_mode: bool) -> Ringer:

    last_name, given_names, title = parse_ringer_name(name)
    while True:
        match choose_option(['Add new ringer', 'Search ringers'] + (['None'] if allow_none else []),
                            default=1) if not quick_mode else 1:
            case 1:
                new_ringer = prompt_add_new_ringer(last_name, given_names, title)
                if new_ringer:
                    return new_ringer
                else:
                    quick_mode = False
            case 2:
                search_last_name = ask('Last name', default=last_name, required=True)
                search_given_names = ask('Given name(s)', default=given_names, required=False)
                potential_ringers = Ringer.get_by_name(search_last_name, search_given_names)
                match len(potential_ringers):
                    case 0:
                        print(f'No existing ringers match (given name: "{search_given_names}", last name: "{search_last_name}")')
                    case 1:
                        if confirm(f'{label}"{name}" -> {potential_ringers[0]}', default=True):
                            return potential_ringers[0]
                    case _:
                        print(f'{len(potential_ringers)} existing ringers match "{(search_given_names + " " + search_last_name).strip()}"')
                        return choose_option(potential_ringers, none_option='None')
            case 3:
                return None


def prompt_add_ringer_by_name_match(name: str, label: str, quick_mode: bool) -> Ringer:

    if name is None:
        return None

    last_name, given_names, _ = parse_ringer_name(name)

    searches = [
        (last_name, given_names, True, quick_mode),
    ]

    if given_names is not None:
        searches += [(last_name, given_names, False, False)]
        fewer_given_names = given_names
        while ' ' in fewer_given_names:
            fewer_given_names = fewer_given_names.rsplit(' ', 1)[0].strip()
            searches += [(last_name, f'{fewer_given_names}%', False, False)]
        searches += [(last_name, f'{given_names[0]}%', False, False)]

    for search_last_name, search_given_names, exact_match, in_quick_mode in searches:

        _logger.debug(f'Attempting to find "{name}" (given name: "{search_given_names}", last name: "{search_last_name}")')

        name_match = Ringer.get_by_name(search_last_name, search_given_names, exact_match=exact_match)
        match len(name_match):
            case 0:
                continue
            case 1:
                if in_quick_mode or confirm(f'{label}"{name}" -> {name_match[0]}', default=True):
                    return name_match[0]
                else:
                    return None
            case _:
                print(f'{label}Found {len(name_match)} ringers matching "{name}" (or aliases)')
                if in_quick_mode:
                    return name_match[0]
                else:
                    return choose_option([f'{r.name} ({r.id})' for r in name_match],
                                         values=name_match,
                                         none_option='None')

    return None


def prompt_add_new_ringer(default_last_name: str, default_given_names: str, default_title: str) -> Ringer:

    default_full_name = f'"{default_last_name}"'
    if default_given_names:
        default_full_name = f'"{default_given_names}" ' + default_full_name
    if default_title:
        default_full_name = f'"{default_title}" ' + default_full_name

    if confirm(None, confirm_message=f'Add new ringer as {default_full_name}?', default=True):
        new_ringer = Ringer(default_last_name, default_given_names, default_title)
    elif confirm(None, confirm_message='Add new ringer with different name?', default=True):
        new_ringer = Ringer(
            ask('Last name', default=default_last_name, required=True),
            ask('Given name(s)', default=default_given_names, required=False),
            ask('Title', default=default_title, required=False)
        )
    else:
        return None

    existing_ringers = Ringer.get_by_name(new_ringer.last_name,
                                          f'{new_ringer.given_names[0]}%' if new_ringer.given_names else None,
                                          exact_match=False)
    if len(existing_ringers) == 0:
        return new_ringer
    else:
        warning(f'Found {len(existing_ringers)} existing ringers with similar names:\n' +
                '\n'.join([f'  - {r.name}' for r in existing_ringers]))
        if confirm(None, confirm_message=f'Add "{new_ringer.name}"?', default=True):
            return new_ringer
        else:
            return None


def prompt_commit_ringer(ringer: Ringer, used_name: str, peal: Peal, quick_mode: bool):

    if ringer.id is None:
        ringer.commit()

    last_name, given_names, _ = parse_ringer_name(used_name)
    stored_name = f'{ringer.given_names} {ringer.last_name}'
    if used_name != stored_name and \
            not ringer.has_alias(last_name=last_name, given_names=given_names):
        if not confirm(None, confirm_message='Add an alias for this ringer?'):
            return
        ringer.add_alias(last_name,
                         given_names,
                         is_primary=choose_option([used_name, stored_name],
                                                  title='Which name should be displayed?',
                                                  default=2) == 1)
        ringer.commit()


def _validate_bell(bell_nums_in_peal: list[int], bell_nums_in_ring: list[int], peal: Peal) -> bool:
    if len(peal.ringers) > 0 and peal.ringers[-1].bell_ids:
        last_bell_num = peal.ring.get_bell_by_id(peal.ringers[-1].bell_ids[-1]).role
        if bell_nums_in_ring[-1] <= last_bell_num:
            error(f'Bell number ({bell_nums_in_ring[-1]}) is not greater than the last bell ({last_bell_num})')
            return False
    for bell in bell_nums_in_ring:
        if peal.ring is not None and peal.ring.num_bells < bell:
            error(f'Bell number ({bell}) exceeds number of bells in the tower')
            return False
        for ringer in peal.ringers:
            if bell in ringer.bell_nums:
                error(f'Bell {bell} already assigned to {ringer.ringer}')
                return False
    if peal.ring is not None and peal.stage is not None:
        max_possible_bells = peal.stage.value + (1 if peal.stage.value % 2 == 1 else 0)
        if max_possible_bells - bell_nums_in_peal[-1] > peal.ring.num_bells - bell_nums_in_ring[-1]:
            error(f'No room for {max_possible_bells - bell_nums_in_peal[-1]} more ringers for performance of {max_possible_bells} ' +
                  f'on {peal.ring.num_bells} bells')
            return False
    return True
