import re
from pypeal.cli.prompts import ask, choose_option, confirm, error
from pypeal.parsers import parse_footnote
from pypeal.peal import MuffleType, Peal


HALF_MUFFLED_REGEX = re.compile(r'.*half\s?\-?\s?muffled.*', re.IGNORECASE)
MUFFLED_REGEX = re.compile(r'.*(?:fully?)?\s?\-?\s?muffled.*', re.IGNORECASE)


def prompt_add_footnote(text: str, peal: Peal, quick_mode: bool):

    for line in text.strip('. ').split('\n'):

        if not quick_mode:
            print(f'Footnote line:\n  > {line}')

        if line.strip('. ').count('.') > 0 and \
                not quick_mode and \
                confirm(None, confirm_message='Split footnote by sentences?', default=False):
            line_parts = line.strip(' ').split('.')
        else:
            line_parts = [line]

        for line_part in line_parts:
            _prompt_add_single_footnote(*parse_footnote(line_part), text, peal, quick_mode)


def prompt_new_footnote(peal: Peal):
    while True:
        if not confirm(None, confirm_message='Add new footnote?', default=False):
            break
        _prompt_add_single_footnote(None, None, None, peal, False)


def prompt_add_muffle_type(peal: Peal):
    if peal.muffles == MuffleType.NONE:
        peal.muffles = choose_option(['None', 'Half-muffled', 'Fully-muffled'],
                                     values=[MuffleType.NONE, MuffleType.HALF, MuffleType.FULL],
                                     default='None',
                                     return_option=True)


def _prompt_add_single_footnote(bells: list[int], text: str, original_text: str, peal: Peal, quick_mode: bool = False):
    ringers = None
    while True:
        if text:
            if original_text is None or text.strip('. ') != original_text.strip('. '):
                ringers = [peal.get_ringer(bell) for bell in bells] if bells else None
                if not quick_mode:
                    print(f'Footnote {len(peal.footnotes) + 1} text:')
                    print(f'  > {text}')
                if bells:
                    print('Referenced ringer(s):')
                    for bell, ringer in zip(bells, ringers):
                        print(f'  - {bell}: {ringer}')
            if quick_mode or confirm(None):
                break
        text, bells = _prompt_footnote_details(bells, text, peal.num_bells, quick_mode)

    muffle_type = MuffleType.NONE
    if re.match(HALF_MUFFLED_REGEX, text):
        muffle_type = MuffleType.HALF
    elif re.match(MUFFLED_REGEX, text):
        muffle_type = MuffleType.FULL
    if muffle_type != MuffleType.NONE and \
            (quick_mode or confirm(f'Possible {muffle_type.name.lower()}-muffled ringing')):
        peal.muffles = muffle_type

    if bells:
        for bell, ringer in zip(bells, ringers):
            peal.add_footnote(text, bell, ringer)
    else:
        peal.add_footnote(text, None, None)


def _prompt_footnote_details(default_bells: list[int],
                             default_text: str,
                             max_bells: int,
                             quick_mode: bool) -> (str, list[int]):
    while True:
        footnote = ask('Footnote text', default=default_text) if not quick_mode else default_text
        if len(footnote.strip()) > 0:
            break
        error('Footnote text cannot be blank')
    if not footnote.endswith('.'):
        footnote += '.'
    bells = None
    while True:
        bells_str = ','.join([str(bell) for bell in default_bells]) if default_bells else None
        if not quick_mode:
            bells_str = ask('Bells (comma-separated)', default=bells_str, required=False)
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
        quick_mode = False
    return (footnote, bells)
