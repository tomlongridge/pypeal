from pypeal import utils
from pypeal.cli.prompts import ask, ask_int, confirm
from pypeal.cli.chooser import choose_option
from pypeal.method import Classification, Method, Stage


def prompt_add_method(method: Method, original_name: str, quick_mode: bool) -> tuple[Method, bool]:

    matched_method: Method = None
    excluded_methods: list[str] = []  # Stores method IDs that have been rejected in a prompt

    if method is not None:
        print(f'Matching method "{original_name or method}"...')
        method_matches = search_method(method)

        match len(method_matches):
            case 0:
                if method:
                    print(f'No methods match "{original_name or method}" (or similar)')
                quick_mode = False
            case 1:
                if quick_mode or confirm(f'Matched "{original_name or method}" to method "{method_matches[0].full_name}"'):
                    return method_matches[0], quick_mode
            case _:
                print(f'{len(method_matches)} methods match "{original_name or method}" (or similar)')
                quick_mode = False
                if matched_method := choose_option(method_matches, none_option='None'):
                    return matched_method, quick_mode
                else:
                    excluded_methods += [m.id for m in method_matches]

    while matched_method is None:

        match choose_option(['Search alternatives', 'Remove method' if method else 'Cancel'], default=1):

            case 1:

                print('Enter search criteria:')
                name = ask('Name', default=method.name if method else None, required=False)
                if state_val := ask_int('Stage', default=method.stage.value if method and method.stage else None, min=2, max=22):
                    stage = Stage(state_val)
                classification = choose_option([classification for classification in Classification],
                                               default=method.classification if method else None,
                                               title='Classification',
                                               none_option='None')
                is_differential = confirm(None, 'Is this a differential method?',
                                          default=method.is_differential if method else None)
                is_little = confirm(None, 'Is this a little method?',
                                    default=method.is_little if method else None)
                is_treble_dodging = confirm(None, 'Is this a treble dodging method?',
                                            default=method.is_treble_dodging if method else None)

                method_matches = list(filter(lambda m: m.id not in excluded_methods,
                                             Method.search(name=name,
                                                           classification=classification,
                                                           stage=stage,
                                                           is_differential=is_differential,
                                                           is_little=is_little,
                                                           is_treble_dodging=is_treble_dodging,
                                                           exact_match=False)))
                match len(method_matches):
                    case 1:
                        matched_method = method_matches[0]
                    case _:
                        print(f'{len(method_matches)} methods match search criteria')
                        quick_mode = False
                        if not (matched_method := choose_option(method_matches, none_option='None')):
                            excluded_methods += [m.id for m in method_matches]

            case 2:
                break

    if matched_method is None and \
            (method is None or confirm('No method matched', confirm_message='Remove this method?')):
        return None, False
    elif matched_method is not None:
        if (method is not None and
                confirm(f'Matched "{original_name or method}" to method "{matched_method.full_name}"')) or \
            (method is None and
                confirm(f'Add "{matched_method.full_name}"')):
            return matched_method, quick_mode


def search_method(method: Method, excluded_methods: list[str] = []) -> list[Method]:

    method_name = utils.get_searchable_string(method.name)

    method_matches = list(filter(lambda m: m.id not in excluded_methods,
                                 Method.search(name=method_name,
                                               classification=method.classification,
                                               stage=method.stage,
                                               is_differential=method.is_differential,
                                               is_little=method.is_little,
                                               is_treble_dodging=method.is_treble_dodging,
                                               exact_match=True)))
    if not method_matches:  # Try without the classification
        method_matches = list(filter(lambda m: m.id not in excluded_methods,
                                     Method.search(name=method_name,
                                                   stage=method.stage,
                                                   is_differential=method.is_differential,
                                                   is_little=method.is_little,
                                                   is_treble_dodging=method.is_treble_dodging,
                                                   exact_match=True)))
    if not method_matches:  # Try with inexact match
        method_matches = list(filter(lambda m: m.id not in excluded_methods,
                                     Method.search(name=method_name,
                                                   stage=method.stage,
                                                   is_differential=method.is_differential,
                                                   is_little=method.is_little,
                                                   is_treble_dodging=method.is_treble_dodging,
                                                   exact_match=False)))

    if len(method_matches) == 2:
        if not method_name.startswith('double') and \
            ((method_matches[0].name.startswith('single') and method_matches[1].name.startswith('double')) or
             (method_matches[0].name.startswith('double') and method_matches[1].name.startswith('single'))) and \
           method_matches[0].name[7:] == method_matches[1].name[7:]:
            return [method_matches[0]]

    return method_matches
