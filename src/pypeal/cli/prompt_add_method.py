from pypeal.cli.prompts import ask, ask_int, choose_option, confirm
from pypeal.method import Method, Stage


def prompt_add_method(method: Method = None, original_title: str = None) -> Method:

    matched_method: Method = None
    exact_match: bool = True
    while matched_method is None:

        if method is not None:
            full_method_match = Method.search(name=method.name,
                                              exact_match=exact_match,
                                              classification=method.classification,
                                              stage=method.stage)
        else:
            full_method_match = []

        match len(full_method_match):
            case 0:
                if method:
                    print(f'No methods match "{method.title}"')
                match choose_option(['Search alternatives'], default=1, cancel_option='Cancel'):
                    case 1:
                        print('Enter search criteria:')
                        name = ask('Name', default=method.name if method else None)
                        stage = Stage(ask_int('Stage', default=method.stage.value if method else None, min=2, max=22))
                        classification_list = ['Bob', 'Place', 'Surprise', 'Treble Bob', 'Treble Place']
                        classification = choose_option(classification_list,
                                                       default=method.classification if method else None,
                                                       return_option=True,
                                                       cancel_option='None')
                        method = Method(None, name=name, classification=classification, stage=stage)
                        exact_match = False
                        continue
                    case None:
                        pass  # Continue to prompt for another go
            case 1:
                matched_method = full_method_match[0]
            case _:
                print(f'{len(full_method_match)} methods match "{method.title}"')
                matched_method = choose_option(full_method_match, cancel_option='None', return_option=True)

        if matched_method is None:
            if method is None or confirm('No method matched', confirm_message=f'Remove "{original_title}"?'):
                return None

    if ((original_title is not None and confirm(f'Matched "{original_title}" to method "{matched_method}" (ID: {matched_method.id})')) or
            (original_title is None and confirm(f'Add "{matched_method}" (ID: {matched_method.id})'))):
        return matched_method
    else:
        return None
