import re
from pypeal.cli.prompt_add_method import prompt_add_method
from pypeal.cli.prompts import ask_int, confirm, warning
from pypeal.entities.method import Classification, Method
from pypeal.parsers import extract_method_type, parse_single_method
from pypeal.entities.peal import Peal

METHOD_LIST_SEPARATORS_REGEX = re.compile(r',|;|\sand\s|&|\n|<br/>|\(\d+\)')
METHOD_PREFIX_IGNORE_REGEX = re.compile(r'^(and\s+|being\s+|\(?\d+(?:\s?methods)?\s?[\)\.:]{1}\s?)', re.IGNORECASE)


def prompt_add_change_of_method_from_string(method_details: str, peal: Peal, quick_mode: bool):

    methods: list[tuple[Method, str, int]] = []
    if method_details:
        if peal.classification == Classification.SURPRISE and \
                (re.match(r'.*standard (?:eight|8).*', method_details, re.IGNORECASE) or
                 (peal.published_title is not None and re.match(r'.*standard (?:eight|8).*', peal.published_title, re.IGNORECASE))):
            methods = add_standard_eight_surprise(peal)
        else:
            last_changes = None
            # Perform 2 splits: first on normal separators, then on numbers followed by a word (e.g "240 Cambridge 360 Yorkshire")
            # this hits a few false positives (e.g London No. 3) but speeds up the majority
            for method_name_split_1 in [detail.strip(' .()') for detail in re.split(METHOD_LIST_SEPARATORS_REGEX, method_details)]:
                for method_name in re.split(r'(\d+\s+\D+)', method_name_split_1):
                    if not method_name:
                        continue
                    method_name = re.sub(METHOD_PREFIX_IGNORE_REGEX, '', method_name, 1)
                    # if there is no name remaining or there are no alphabetical characters, it is not a method name
                    if not method_name or not re.search(r'[a-zA-Z]', method_name):
                        continue
                    method_obj = Method(None)
                    method_obj.stage, method_obj.classification, method_obj.name, changes = parse_single_method(method_name)
                    extract_method_type(method_obj)
                    if not method_obj.stage:
                        method_obj.stage = peal.stage
                    if not method_obj.classification:
                        method_obj.classification = peal.classification
                    methods.append((method_obj, method_name, changes or last_changes))
                    last_changes = changes or last_changes

    prompt_add_change_of_method(methods, peal, quick_mode)


def prompt_add_change_of_method(method_details: list[tuple[Method, str, int]], peal: Peal, quick_mode: bool):

    print('Adding changes of methods to multi-method peal...')
    original_num_methods = len(peal.methods)

    # Parse method details
    if method_details:  # method_details is None if no methods were listed but it is a multi-method peal in title

        for method_obj, original_name, changes in method_details:
            default_changes = peal.methods[-1][1] if len(peal.methods) > 0 else None
            quick_mode = prompt_add_method(method_obj, original_name, changes or default_changes, peal, quick_mode)

    # Prompt for additional methods
    while True:
        if quick_mode or \
           not confirm(None,
                       confirm_message='Add more changes of method?' if method_details else 'Add changes of method?',
                       default=len(peal.methods) < peal.num_methods_in_title):
            break
        elif len(peal.methods) >= peal.num_methods_in_title:
            warning(f'Number of methods ({len(peal.methods)}) does not match number of methods from peal title ' +
                    f'({peal.num_methods_in_title}).')
            if not confirm(None, confirm_message='Do you want to add more?', default=False):
                break
        default_changes = peal.methods[-1][1] if len(peal.methods) > 0 else None
        quick_mode = prompt_add_method(None, None, default_changes, peal, quick_mode)

    # Potentially update number of methods in the peal title if they now do not match
    while len(peal.methods) != original_num_methods and len(peal.methods) != peal.num_methods_in_title:
        warning(f'Number of methods ({len(peal.methods)}) does not match number of methods from peal title ' +
                f'({peal.num_methods_in_title}).')
        if confirm(None, confirm_message='Do you want to update the title?'):
            peal.num_methods = ask_int('Number of methods', default=len(peal.methods) or 0)
            peal.num_principles = ask_int('Number of principles', default=peal.num_principles or 0)
            peal.num_variants = ask_int('Number of variants', default=peal.num_variants or 0)
        else:
            break

    # Validate the changes added for each method against the number for the peal
    total_changes = 0
    for method in peal.methods:
        if method[1] is not None:
            total_changes += method[1]

    if total_changes > 0 and \
            (peal.changes or 0) != total_changes and \
            confirm(f'Peal has {peal.changes or 0} changes, but {total_changes} have been added in method details',
                    confirm_message=f'Update peal changes to {total_changes}?',
                    default=True):
        peal.changes = total_changes


def add_standard_eight_surprise(peal: Peal) -> list[tuple[Method, str, int]]:
    methods: list[tuple[Method, str, int]] = []
    methods.append((
        Method.search('Cambridge', stage=peal.stage, classification=Classification.SURPRISE, is_little=False, exact_match=True)[0],
        'Cambridge',
        None
    ))
    methods.append((
        Method.search('Yorkshire', stage=peal.stage, classification=Classification.SURPRISE, is_little=False, exact_match=True)[0],
        'Yorkshire',
        None
    ))
    methods.append((
        Method.search('Lincolnshire', stage=peal.stage, classification=Classification.SURPRISE, is_little=False, exact_match=True)[0],
        'Lincolnshire',
        None
    ))
    methods.append((
        Method.search('Superlative' if peal.stage != 10 else 'Superlative No 2',
                      stage=peal.stage,
                      classification=Classification.SURPRISE,
                      is_little=False,
                      exact_match=True)[0],
        'Superlative',
        None
    ))
    methods.append((
        Method.search('Rutland', stage=peal.stage, classification=Classification.SURPRISE, is_little=False, exact_match=True)[0],
        'Rutland',
        None
    ))
    methods.append((
        Method.search('Pudsey', stage=peal.stage, classification=Classification.SURPRISE, is_little=False, exact_match=True)[0],
        'Pudsey',
        None
    ))
    methods.append((
        Method.search('Bristol', stage=peal.stage, classification=Classification.SURPRISE, is_little=False, exact_match=True)[0],
        'Bristol',
        None
    ))
    methods.append((
        Method.search('London' if peal.stage != 10 else 'London No 3', stage=peal.stage, classification=Classification.SURPRISE, is_little=False, exact_match=True)[0],
        'London',
        None
    ))
    return methods
