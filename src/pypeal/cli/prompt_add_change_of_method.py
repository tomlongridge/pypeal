import re
from pypeal.cli.prompt_add_method import prompt_add_method
from pypeal.cli.prompts import ask_int, confirm
from pypeal.method import Method
from pypeal.parsers import parse_single_method
from pypeal.peal import Peal


def prompt_add_change_of_method(method_details: str, peal: Peal, quick_mode: bool):

    print('Adding changes of methods to multi-method peal...')
    method_count: int = 0

    if method_details:  # method_details is None if no methods were listed but it is a multi-method peal in title

        for method in [detail.strip() for detail in re.split(r',|;', method_details)]:

            method_obj = Method(None)
            method_obj.stage, method_obj.classification, method_obj.name, changes = parse_single_method(method)
            if not method_obj.stage:
                method_obj.stage = peal.stage
            if not method_obj.classification:
                method_obj.classification = peal.classification

            new_method, quick_mode = prompt_add_method(method_obj, method, quick_mode)
            if not new_method:
                quick_mode = False
                continue

            if not quick_mode:
                changes = ask_int('Number of changes', default=changes)
            peal.add_method(new_method, changes)
            method_count += 1
            print(f'Method {method_count}: {new_method.title} ({changes if changes else "unknown"} changes)')

    while True:
        if quick_mode or \
           not confirm(None,
                       confirm_message='Add more changes of method?' if method_details else 'Add changes of method?',
                       default=len(peal.methods) < peal.num_methods_in_title):
            break
        elif len(peal.methods) >= peal.num_methods_in_title and \
                not confirm(f'Number of methods ({method_count}) does not match number of methods from peal title ' +
                            f'({peal.num_methods_in_title}).',
                            confirm_message='Do you want to add more?',
                            default=False):
            break
        method, quick_mode = prompt_add_method(None, None, quick_mode)
        if method:
            changes = ask_int('Number of changes', default=None)
            peal.add_method(method, changes)
            method_count += 1
            print(f'Method {method_count}: {method.title} ({changes if changes else "unknown"} changes)')
