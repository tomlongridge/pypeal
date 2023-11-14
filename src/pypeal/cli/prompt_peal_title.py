from pypeal.cli.prompts import ask, ask_int, choose_option, confirm
from pypeal.method import Method, Stage
from pypeal.parsers import parse_method_title
from pypeal.peal import Peal, PealType


def prompt_peal_title(title: str, peal: Peal, quick_mode: bool):

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
        parsed_method: Method
        parsed_method, is_spliced, is_mixed, num_methods, \
            num_variants, num_principles = parse_method_title(title)

        # We haven't matched a method but it's not multi-method, start a single method search
        # (note - "is not True" here is correct as if it's None we want to do this)
        if is_spliced is not True and is_mixed is not True:

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
                        set_peal_title(peal, full_method_match[0], PealType.SINGLE_METHOD)
                    else:
                        set_peal_title(peal,
                                       choose_option(non_exact_method_match, cancel_option='None', return_option=True),
                                       PealType.SINGLE_METHOD)
                    if peal.method:
                        return

        # If it's not clear from the title, prompt for multi-method peal
        if not quick_mode and (is_spliced is None or is_mixed is None):
            is_spliced = confirm(None,
                                 confirm_message='Is this a spliced peal?',
                                 default=False if is_spliced is None else is_spliced)
            if is_spliced:
                is_mixed = False
            else:
                is_mixed = confirm(None,
                                   confirm_message='Is this a mixed peal?',
                                   default=False if is_mixed is None else is_mixed)
                if not is_mixed:
                    if confirm(None, confirm_message='Is this a (non-peal) general performance?', default=False):
                        set_peal_title(peal, title, PealType.GENERAL_RINGING)
                        return

        # Search for a single method
        if is_spliced is False and is_mixed is False:

            print(f'Unable to match single method from title "{title}". Please enter search criteria manually:')
            quick_mode = False

            name = ask('Name', default=parsed_method.name, required=False)
            stage = Stage(ask_int('Stage', default=parsed_method.stage.value if parsed_method.stage else None, min=2, max=22))
            classification = choose_option(['Bob', 'Place', 'Surprise', 'Delight', 'Treble Bob', 'Treble Place'],
                                           default=parsed_method.classification,
                                           return_option=True)
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
        if is_spliced or is_mixed:

            print(f'Multi-method peal: "{title}"...')

            stage = parsed_method.stage
            classification = parsed_method.classification
            is_variable_cover = False

            if not quick_mode:
                while True:
                    num_methods = ask_int('Number of methods', default=num_methods or 0)
                    num_principles = ask_int('Number of principles', default=num_principles or 0)
                    num_variants = ask_int('Number of variants', default=num_variants or 0)
                    if num_methods + num_principles + num_variants > 0:
                        break
                stage = Stage(ask_int('Stage', default=stage.value if stage else None, min=2, max=22))
                classification = choose_option(['Bob', 'Place', 'Surprise', 'Delight', 'Treble Bob', 'Treble Place', None],
                                               default=classification,
                                               return_option=True)
                if classification is None:
                    is_variable_cover = confirm(None, 'Is this peal variable cover?', default=is_variable_cover)

            set_peal_title(peal,
                           None,
                           PealType.MIXED_METHODS if is_mixed else PealType.SPLICED_METHODS,
                           stage,
                           classification,
                           num_methods,
                           num_principles,
                           num_variants,
                           is_variable_cover)
            return

        # All options abandoned, loop round again
        print('No peal title matched or entered. Trying again...')
        quick_mode = False


def set_peal_title(peal: Peal,
                   title: any,
                   peal_type: PealType,
                   stage: Stage = None,
                   classification: str = None,
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
        peal.description = None
        peal.method = None
    elif type(title) is str:
        peal.description = title
        peal.method = None
    elif type(title) is Method:
        peal.description = None
        peal.method = title
        peal.stage = title.stage
        peal.classification = title.classification
