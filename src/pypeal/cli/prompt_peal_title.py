from pypeal.cli.prompts import ask, ask_int, choose_option, confirm
from pypeal.method import Method, Stage
from pypeal.parsers import parse_method_title
from pypeal.peal import Peal


def prompt_peal_title(title: str, peal: Peal):

    while True:

        print(f'Matching peal titled "{title}"...')

        # Attempt an easy match against a single method using the exact title
        if title:
            full_method_match = Method.get_by_name(title)
            match len(full_method_match):
                case 0:
                    # Continue to non-exact search
                    pass
                case 1:
                    if confirm(f'Matched "{title}" to method "{full_method_match[0]}" (ID: {full_method_match[0].id})'):
                        set_peal_title(peal, full_method_match[0])
                        return
                case _:
                    print(f'{len(full_method_match)} methods match "{title}"')
                    set_peal_title(peal, choose_option(full_method_match, cancel_option='None', return_option=True))
                    if peal.method:
                        return

        # Parse method title for inspiration and future search
        parsed_method: Method
        parsed_method, peal.is_spliced, peal.is_mixed, peal.num_methods, \
            peal.num_variants, peal.num_principles = parse_method_title(title)

        # We haven't matched a method but it's not multi-method, start a single method search
        # (note - "is not True" here is correct as if it's None we want to do this)
        if peal.is_spliced is not True and peal.is_mixed is not True:

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
                    if confirm(f'Matched "{title}" to method "{non_exact_method_match[0]}" (ID: {non_exact_method_match[0].id})'):
                        set_peal_title(peal, non_exact_method_match[0])
                        return
                case _:
                    print(f'{len(non_exact_method_match)} methods match "{parsed_method}"')
                    set_peal_title(peal, choose_option(non_exact_method_match, cancel_option='None', return_option=True))
                    if peal.method:
                        return

        # If it's not clear from the title, prompt for multi-method peal
        if peal.is_spliced is None or peal.is_mixed is None:
            peal.is_spliced = confirm(None, confirm_message='Is this a spliced peal?', default=peal.is_spliced)
            peal.is_mixed = False
            if not peal.is_spliced:
                peal.is_mixed = confirm(None, confirm_message='Is this a mixed peal?', default=peal.is_mixed)

        # Search for a single method
        if peal.is_spliced is False and peal.is_mixed is False:

            print(f'Unable to match single method from title "{title}". Please enter search criteria manually:')

            name = ask('Name', default=parsed_method.name, required=False)
            stage = Stage(ask_int('Stage', default=parsed_method.stage.value, min=2, max=22))
            classification = choose_option(['Bob', 'Place', 'Surprise', 'Treble Bob', 'Treble Place'],
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
                        set_peal_title(peal, user_search_match[0])
                        return
                case _:
                    print(f'{len(user_search_match)} methods match search criteria')
                    set_peal_title(peal, choose_option(full_method_match, cancel_option='None', return_option=True))
                    if peal.method:
                        return

        # Add multi-method title
        if peal.is_spliced or peal.is_mixed:

            peal.stage = parsed_method.stage
            peal.classification = parsed_method.classification

            while True:
                peal.num_methods = ask_int('Number of methods', default=peal.num_methods)
                peal.num_principles = ask_int('Number of principles', default=peal.num_principles)
                peal.num_variants = ask_int('Number of variants', default=peal.num_variants)
                if peal.num_methods_in_title > 0:
                    break
            peal.stage = Stage(ask_int('Stage', default=peal.stage.value if peal.stage else None, min=2, max=22))
            peal.classification = choose_option(['Bob', 'Place', 'Surprise', 'Treble Bob', 'Treble Place', None],
                                                default=peal.classification,
                                                return_option=True)
            if peal.classification is None:
                peal.is_variable_cover = confirm(None, 'Is this peal variable cover?', default=False)

            if confirm(f'{peal.method_title}'):
                peal.title = None
                peal.method = None
                return

        # All options abandoned, loop round again
        print('No peal title matched or entered. Trying again...')


def set_peal_title(peal: Peal, title: any):
    if title is None:
        return
    peal.is_mixed = False
    peal.is_spliced = False
    peal.is_variable_cover = False
    peal.num_methods = 0
    peal.num_principles = 0
    peal.num_variants = 0
    if type(title) is str:
        peal.title = title
        peal.method = None
    elif type(title) is Method:
        peal.title = None
        peal.method = title
        peal.stage = title.stage
        peal.classification = title.classification
