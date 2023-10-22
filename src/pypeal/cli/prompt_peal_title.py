from pypeal.cli.prompts import ask, ask_int, choose_option, confirm
from pypeal.method import Method, Stage
from pypeal.peal import Peal


def prompt_peal_title(peal: Peal):

    print(f'Matching peal titled "{peal.method_title}"...')

    # Attempt an easy match against a single method using the exact title
    if peal.title:
        full_method_match = Method.search(name=peal.title, exact_match=True, classification=peal.classification, stage=peal.stage)
        match len(full_method_match):
            case 0:
                # Continue to search
                pass
            case 1:
                if confirm(f'Matched "{peal.method_title}" to method "{full_method_match[0]}" (ID: {full_method_match[0].id})'):
                    peal.method = full_method_match[0]
                    peal.title = None
                    peal.is_mixed = False
                    peal.is_spliced = False
                    return
            case _:
                print(f'{len(full_method_match)} methods match "{peal.method_title}"')
                peal.method = choose_option(full_method_match, cancel_option='None', return_option=True)
                peal.title = None
                peal.is_mixed = False
                peal.is_spliced = False
                return

    # If it's not clear from the title, prompt for multi-method peal
    if peal.is_spliced is None or peal.is_mixed is None:
        peal.is_spliced = confirm(None, confirm_message='Is this a spliced peal?', default=peal.is_spliced)
        peal.is_mixed = False
        if not peal.is_spliced:
            peal.is_mixed = confirm(None, confirm_message='Is this a mixed peal?', default=peal.is_mixed)
            if not peal.is_mixed:
                if confirm(f'Other performance: {peal.method_title}', default=True):
                    peal.title = peal.method_title
                    peal.classification = None
                    peal.stage = None
                    peal.method = None
                    return

    # We haven't matched a method but it's not multi-method, start a single method search
    if peal.is_spliced is False and peal.is_mixed is False:

        while not peal.method:

            print(f'Attempting to match single method "{peal.title}"')

            match choose_option(['Search alternatives', 'Change to mixed methods', 'Change to spliced methods'],
                                default=1,
                                cancel_option='Cancel'):
                case 1:
                    name = ask('Name', default=peal.title if peal.title else None)
                    stage = Stage(ask_int('Stage', default=peal.stage.value, min=2, max=22))
                    classification = choose_option(['Bob', 'Place', 'Surprise', 'Treble Bob', 'Treble Place'],
                                                   default=peal.classification,
                                                   return_option=True)
                    potential_methods = Method.search(name=name, classification=classification, stage=stage)
                    print(f'{len(potential_methods)} methods match')
                    peal.method = choose_option(potential_methods, cancel_option='None', return_option=True)
                case 2:
                    peal.is_mixed = True
                    peal.is_spliced = False
                    prompt_peal_title(peal)
                    return
                case 3:
                    peal.is_spliced = True
                    peal.is_mixed = False
                    prompt_peal_title(peal)
                    return
                case None:
                    return

        peal.title = None
        return

    # Multi-method peal - remove title
    peal.title = None

    while True:

        while True:
            peal.num_methods = ask_int('Number of methods', default=peal.num_methods)
            peal.num_principles = ask_int('Number of principles', default=peal.num_principles)
            peal.num_variants = ask_int('Number of variants', default=peal.num_variants)
            if peal.num_methods + peal.num_principles + peal.num_variants > 0:
                break
        peal.stage = Stage(ask_int('Stage', default=peal.stage.value, min=2, max=22))
        peal.classification = choose_option(['Bob', 'Place', 'Surprise', 'Treble Bob', 'Treble Place', None],
                                            default=peal.classification,
                                            return_option=True)
        if peal.classification is None:
            peal.is_variable_cover = confirm(None, 'Is this peal variable cover?', default=False)

        if confirm(f'{peal.method_title}'):
            peal.title = None
            peal.method = None
            break
