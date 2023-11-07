import re
from pypeal.cli.prompts import ask, confirm, error
from pypeal.parsers import parse_footnote
from pypeal.peal import Peal


def prompt_add_footnote(text: str, peal: Peal):

    for line in text.strip('. ').split('\n'):

        print(f'Footnote line:\n  > {line}')

        if line.strip('. ').count('.') > 0 and confirm(None, confirm_message='Split footnote by sentences?'):
            line_parts = line.strip(' ').split('.')
        else:
            line_parts = [line]

        for line_part in line_parts:
            prompt_add_single_footnote(*parse_footnote(line_part), text, peal)


def prompt_new_footnote(peal: Peal):
    while True:
        if not confirm(None, confirm_message='Add new footnote?', default=False):
            break
        prompt_add_single_footnote(None, None, None, peal)


def prompt_add_single_footnote(bells: list[int], text: str, original_text: str, peal: Peal):
    ringers = None
    while True:
        if text:
            if original_text is None or text.strip('. ') != original_text.strip('. '):
                ringers = [peal.get_ringer(bell) for bell in bells] if bells else None
                print(f'Footnote {len(peal.footnotes) + 1} text:')
                print(f'  > {text}')
                if bells:
                    print('Referenced ringer(s):')
                    for bell, ringer in zip(bells, ringers):
                        print(f'  - {bell}: {ringer}')
            if confirm(None):
                break
        text, bells = prompt_footnote_details(default_text=text, default_bells=bells, max_bells=peal.num_bells)

    if bells:
        for bell, ringer in zip(bells, ringers):
            peal.add_footnote(text, bell, ringer)
    else:
        peal.add_footnote(text, None, None)


def prompt_footnote_details(default_bells: list[int] = None, default_text: str = None, max_bells: int = None) -> (str, list[int]):
    while True:
        footnote = ask('Footnote text', default=default_text)
        if len(footnote.strip()) > 0:
            break
        error('Footnote text cannot be blank')
    if not footnote.endswith('.'):
        footnote += '.'
    bells = None
    while True:
        bells_str = ask('Bells (comma-separated)',
                        default=','.join([str(bell) for bell in default_bells]) if default_bells else None,
                        required=False)
        if not bells_str:
            break
        elif re.match(r'^([0-9]+,?)+$', bells_str):
            bells = []
            for bell in bells_str.split(','):
                if int(bell) < 1 or int(bell) > max_bells:
                    print(f'Invalid bell number: {bell}')
                    break
                else:
                    bells.append(int(bell))
            else:
                break
        error(f'Bells must be a comma-separated list of numbers less than or equal to {max_bells}')
    return (footnote, bells)
