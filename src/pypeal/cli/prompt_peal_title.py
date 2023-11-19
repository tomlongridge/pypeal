from pypeal.cli.prompt_add_change_of_method import prompt_add_change_of_method
from pypeal.cli.prompts import ask, ask_int, choose_option, confirm
from pypeal.method import Classification, Method, Stage
from pypeal.parsers import parse_method_title
from pypeal.peal import Peal, PealType
from pypeal.utils import strip_internal_space


def prompt_peal_title(title: str, peal: Peal, quick_mode: bool):

    title = strip_internal_space(title)

    peal.description = title

    while True:

        # Attempt an easy match against a single method using the exact title
        if title:
            full_method_match = Method.get_by_name(title)
            match len(full_method_match):
                case 0:
                    # Continue to non-exact search
                    pass
                case 1:
                    if quick_mode or confirm(f'Matched "{title}" to method "{full_method_match[0]}" (ID: {full_method_match[0].id})'):
                        set_peal_title(peal, full_method_match[0], PealType.SINGLE_METHOD)
                        return
                case _:
                    print(f'{len(full_method_match)} methods match "{title}"')
                    if quick_mode:
                        set_peal_title(peal, full_method_match[0], PealType.SINGLE_METHOD)
                    else:
                        set_peal_title(peal,
                                       choose_option(full_method_match, cancel_option='None', return_option=True),
                                       PealType.SINGLE_METHOD)
                    if peal.method:
                        return

        print(f'Matching peal titled "{title}"...')

        # Parse method title for inspiration and future search
        parsed_methods: list[Method]
        parsed_methods, peal_type, num_methods, \
            num_variants, num_principles = parse_method_title(title)

        # We haven't matched a method but it's not multi-method, try a single (inexact) method search
        # e.g. a single method spelt differently
        if peal_type in [None, PealType.SINGLE_METHOD]:

            parsed_method = parsed_methods[0]

            # Attempt non-exact search using name parsed from title
            non_exact_method_match = Method.search(name=parsed_method.name,
                                                   classification=parsed_method.classification,
                                                   stage=parsed_method.stage,
                                                   is_differential=parsed_method.is_differential,
                                                   is_little=parsed_method.is_little,
                                                   is_treble_dodging=parsed_method.is_treble_dodging,
                                                   exact_match=False)
            match len(non_exact_method_match):
                case 0:
                    # Continue to search
                    pass
                case 1:
                    if quick_mode or \
                            confirm(f'Matched "{title}" to method "{non_exact_method_match[0]}" (ID: {non_exact_method_match[0].id})'):
                        set_peal_title(peal, non_exact_method_match[0], PealType.SINGLE_METHOD)
                        return
                case _:
                    print(f'{len(non_exact_method_match)} methods match "{parsed_method}"')
                    if quick_mode:
                        set_peal_title(peal, non_exact_method_match[0], PealType.SINGLE_METHOD)
                    else:
                        set_peal_title(peal,
                                       choose_option(non_exact_method_match, cancel_option='None', return_option=True),
                                       PealType.SINGLE_METHOD)
                    if peal.method:
                        return

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
                                      [pt for pt in PealType],
                                      'What kind of peal is being rung?',
                                      default=default_peal_type.name.title().replace('_', ' '),
                                      return_option=True)

        if peal_type == PealType.GENERAL_RINGING:
            set_peal_title(peal, title, PealType.GENERAL_RINGING)
            return

        # Interactive search for a single method
        if peal_type == PealType.SINGLE_METHOD:

            parsed_method = parsed_methods[0]

            print(f'Unable to match single method from title "{title}". Please enter search criteria manually:')
            quick_mode = False

            name = ask('Name', default=parsed_method.name, required=False)
            stage = Stage(ask_int('Stage', default=parsed_method.stage.value if parsed_method.stage else None, min=2, max=22))
            classification = choose_option([classification for classification in Classification],
                                           default=parsed_method.classification or 'None',
                                           return_option=True,
                                           cancel_option='None')
            is_differential = confirm(None, 'Is this a differential method?', default=parsed_method.is_differential)
            is_little = confirm(None, 'Is this a little method?', default=parsed_method.is_little)
            is_treble_dodging = confirm(None, 'Is this a treble dodging method?', default=parsed_method.is_treble_dodging)
            user_search_match = Method.search(name=name,
                                              classification=classification,
                                              stage=stage,
                                              is_differential=is_differential,
                                              is_little=is_little,
                                              is_treble_dodging=is_treble_dodging,
                                              exact_match=False)
            match len(user_search_match):
                case 0:
                    # Fall-through
                    pass
                case 1:
                    if confirm(f'Matched "{title}" to method "{user_search_match[0]}" (ID: {user_search_match[0].id})'):
                        set_peal_title(peal, user_search_match[0], PealType.SINGLE_METHOD)
                        return
                case _:
                    print(f'{len(user_search_match)} methods match search criteria')
                    set_peal_title(peal,
                                   choose_option(full_method_match, cancel_option='None', return_option=True),
                                   PealType.SINGLE_METHOD)
                    if peal.method:
                        return

        # Add multi-method title
        if peal_type in [PealType.MIXED_METHODS, PealType.SPLICED_METHODS]:

            print(f'Multi-method peal: "{title}"...')

            is_variable_cover = False
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
                case 0:
                    stage = None
                    classification = None

            if not quick_mode:
                while True:
                    num_methods = ask_int('Number of methods', default=num_methods or 0)
                    num_principles = ask_int('Number of principles', default=num_principles or 0)
                    num_variants = ask_int('Number of variants', default=num_variants or 0)
                    if num_methods + num_principles + num_variants > 0:
                        break
                stage = Stage(ask_int('Stage', default=stage.value if stage else None, min=2, max=22))
                classification = choose_option([classification for classification in Classification],
                                               default=classification or 'None',
                                               cancel_option='None',
                                               return_option=True)
                if classification is None:
                    is_variable_cover = confirm(None, 'Is this peal variable cover?', default=is_variable_cover)

            set_peal_title(peal,
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
                prompt_add_change_of_method([(method, None) for method in parsed_methods], peal, quick_mode)

            return

        # All options abandoned, loop round again
        print('No peal title matched or entered. Trying again...')
        quick_mode = False


def set_peal_title(peal: Peal,
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
    elif type(title) is Method:
        peal.method = title
        peal.stage = title.stage
        peal.classification = Classification(title.classification) if title.classification else None
