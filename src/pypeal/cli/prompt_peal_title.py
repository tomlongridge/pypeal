from pypeal.cli.prompt_add_change_of_method import prompt_add_change_of_method
from pypeal.cli.prompt_add_method import search_method
from pypeal.cli.prompts import ask, ask_int, confirm, error
from pypeal.cli.chooser import choose_option
from pypeal.entities.method import Classification, Method, Stage
from pypeal.parsers import parse_method_title
from pypeal.entities.peal import Peal, PealType


def prompt_peal_title(title: str, peal: Peal, quick_mode: bool):

    peal.published_title = title
    print(f'Matching peal titled "{title}"...')

    excluded_methods: list[str] = []  # Stores method IDs that have been rejected in a prompt

    method_matches: list[Method]
    parsed_methods: list[Method]

    while True:

        # Attempt an easy match against a single method using the exact title
        named_method_match: Method = Method.get_by_name(title)
        if named_method_match and named_method_match.id not in excluded_methods:

            if quick_mode or confirm(f'Matched "{title}" to method "{named_method_match}" (ID: {named_method_match.id})'):
                _set_peal_title(peal, named_method_match, PealType.SINGLE_METHOD)
                return
            else:
                excluded_methods.append(named_method_match.id)

        # Parse method title for inspiration and future search
        parsed_methods, peal_type, num_methods, \
            num_variants, num_principles = parse_method_title(title)

        # We haven't matched a method but it's not multi-method, try a single (inexact) method search
        # e.g. a single method spelt differently
        if peal_type in [None, PealType.SINGLE_METHOD]:

            parsed_method = parsed_methods[0]

            # Attempt non-exact search using name parsed from title
            method_matches = search_method(parsed_method)
            match len(method_matches):
                case 0:
                    # Continue to search
                    pass
                case 1:
                    if quick_mode or \
                            confirm(f'Matched "{title}" to method "{method_matches[0]}" (ID: {method_matches[0].id})'):
                        _set_peal_title(peal, method_matches[0], PealType.SINGLE_METHOD)
                        return
                    else:
                        excluded_methods.append(method_matches[0].id)
                case _:
                    print(f'{len(method_matches)} methods match "{parsed_method}" [{len(excluded_methods)} methods excluded]')
                    quick_mode = False
                    _set_peal_title(peal,
                                    choose_option(method_matches, none_option='None'),
                                    PealType.SINGLE_METHOD)
                    if peal.method:
                        return
                    else:
                        excluded_methods += [m.id for m in method_matches]

        # Prompt for peal type as we haven't matched a single method yet
        # (use parsed spliced/mixed for quick mode but allow to change it for prompt mode)
        if not quick_mode or peal_type in [None, PealType.SINGLE_METHOD]:
            default_peal_type = PealType.SINGLE_METHOD
            if (parsed_methods[0].name is None) or \
                    ((num_methods or 0) + (num_variants or 0) + (num_principles or 0) > 1):
                if parsed_methods[0].stage.value <= Stage.DOUBLES.value:
                    default_peal_type = PealType.MIXED_METHODS
                else:
                    default_peal_type = PealType.SPLICED_METHODS

            peal_type = choose_option([pt.name.title().replace('_', ' ') for pt in PealType],
                                      values=[pt for pt in PealType],
                                      title='What kind of peal is being rung?',
                                      default=default_peal_type)

        if peal_type == PealType.GENERAL_RINGING:
            _set_peal_title(peal, title, PealType.GENERAL_RINGING)
            return

        # Interactive search for a single method
        if peal_type == PealType.SINGLE_METHOD:

            parsed_method = parsed_methods[0]

            print(f'Unable to match single method from title "{title}". Please enter search criteria manually:')
            quick_mode = False

            name = ask('Name', default=parsed_method.name, required=False)

            # Attempt to parse the entered name as a full method name and use the parts if found
            prompt_methods, _, _, _, _ = parse_method_title(name)
            if prompt_methods[0].stage is not None:
                stage = prompt_methods[0].stage
            else:
                stage = Stage(ask_int('Stage', default=parsed_method.stage.value if parsed_method.stage else None, min=2, max=22))
            if prompt_methods[0].classification is not None:
                classification = prompt_methods[0].classification
            else:
                classification = choose_option([classification for classification in Classification],
                                               default=parsed_method.classification,
                                               title='Classification',
                                               none_option='None')
            if prompt_methods[0].is_differential is not None:
                is_differential = prompt_methods[0].is_differential
            else:
                is_differential = confirm(None, 'Is this a differential method?', default=parsed_method.is_differential)
            if prompt_methods[0].is_little is not None:
                is_little = prompt_methods[0].is_little
            else:
                is_little = confirm(None, 'Is this a little method?', default=parsed_method.is_little)
            if prompt_methods[0].is_treble_dodging is not None:
                is_treble_dodging = prompt_methods[0].is_treble_dodging
            else:
                is_treble_dodging = confirm(None, 'Is this a treble dodging method?', default=parsed_method.is_treble_dodging)

            method_matches = list(filter(lambda m: m.id not in excluded_methods,
                                         Method.search(name=name,
                                                       classification=classification,
                                                       stage=stage,
                                                       is_differential=is_differential,
                                                       is_little=is_little,
                                                       is_treble_dodging=is_treble_dodging,
                                                       exact_match=False)))
            match len(method_matches):
                case 0:
                    # Fall-through
                    pass
                case 1:
                    if confirm(f'Matched "{title}" to method "{method_matches[0]}" (ID: {method_matches[0].id})'):
                        _set_peal_title(peal, method_matches[0], PealType.SINGLE_METHOD)
                        return
                    else:
                        excluded_methods += method_matches[0].id
                case _:
                    print(f'{len(method_matches)} methods match search criteria [{len(excluded_methods)} methods excluded]')
                    if matched_method := choose_option(method_matches, none_option='None'):
                        _set_peal_title(peal,
                                        matched_method,
                                        PealType.SINGLE_METHOD)
                        return
                    else:
                        excluded_methods += [m.id for m in method_matches]

        # Add multi-method title
        if peal_type in [PealType.MIXED_METHODS, PealType.SPLICED_METHODS]:

            print(f'Multi-method peal: "{title}"...')

            is_variable_cover = False
            stage = None
            classification = None
            match len(parsed_methods):
                case 2:
                    stage = parsed_methods[0].stage
                    if parsed_methods[0].stage != parsed_methods[1].stage:
                        is_variable_cover = True
                    if parsed_methods[0].classification == parsed_methods[1].classification:
                        classification = parsed_methods[0].classification
                case 1:
                    stage = parsed_methods[0].stage
                    classification = parsed_methods[0].classification

            # Bob and Place methods aren't usually specified in the title
            if classification in [Classification.BOB, Classification.PLACE]:
                classification = None

            if not quick_mode:
                while True:
                    num_methods = ask_int('Number of methods', default=num_methods or 0)
                    num_principles = ask_int('Number of principles', default=num_principles or 0)
                    num_variants = ask_int('Number of variants', default=num_variants or 0)
                    if num_methods + num_principles + num_variants > 0:
                        break
                stage_val = ask_int('Stage', default=stage.value if stage else None, min=2, max=22)
                stage = Stage(stage_val) if stage_val else None
                classification = choose_option([classification for classification in Classification],
                                               default=classification,
                                               title='Classification',
                                               none_option='None')
                if classification is None:
                    is_variable_cover = confirm(None, 'Is this peal variable cover?', default=is_variable_cover)

            _set_peal_title(peal,
                            None,
                            peal_type,
                            stage,
                            classification,
                            num_methods,
                            num_principles,
                            num_variants,
                            is_variable_cover)

            # We have identified two methods from the title - add them to method details
            if len(parsed_methods) > 1:
                prompt_add_change_of_method([(method, None, None) for method in parsed_methods], peal, quick_mode)

            return

        # All options abandoned, loop round again
        error('No peal title matched or entered. Trying again...')
        quick_mode = False
        excluded_methods.clear()


def _set_peal_title(peal: Peal,
                    title: any,
                    peal_type: PealType,
                    stage: Stage = None,
                    classification: Classification = None,
                    num_methods: int = None,
                    num_principles: int = None,
                    num_variants: int = None,
                    is_variable_cover: bool = False):
    peal.type = peal_type
    peal.stage = stage
    peal.classification = classification
    peal.is_variable_cover = is_variable_cover
    peal.num_methods = num_methods
    peal.num_principles = num_principles
    peal.num_variants = num_variants
    if title is None:
        peal.method = None
    elif type(title) is str:
        peal.method = None
        peal.title = title
    elif type(title) is Method:
        peal.method = title
        peal.stage = title.stage
        peal.classification = Classification(title.classification) if title.classification else None
