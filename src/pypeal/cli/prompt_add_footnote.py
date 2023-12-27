import re
from pypeal.cli.prompt_add_composition_details import prompt_add_composition_details
from pypeal.cli.prompts import ask, confirm, error, warning
from pypeal.cli.chooser import choose_option
from pypeal.parsers import parse_footnote, parse_footnote_for_composer
from pypeal.peal import MuffleType, Peal


HALF_MUFFLED_REGEX = re.compile(r'.*half\s?\-?\s?muffled.*', re.IGNORECASE)
MUFFLED_REGEX = re.compile(r'.*(?:fully?)?\s?\-?\s?muffled.*', re.IGNORECASE)


def prompt_add_footnote(text: str, peal: Peal, quick_mode: bool):

    if text:
        for line in text.strip('. ').split('\n'):

            if line.strip('. ').count('. ') > 0 and \
                    (quick_mode or
                        confirm(f'Footnote line:\n  > {line}', confirm_message='Split footnote by sentences?', default=True)):
                line_parts = line.strip(' ').split('. ')
            else:
                line_parts = [line]

            for line_part in line_parts:
                composer_name = parse_footnote_for_composer(line_part)
                if composer_name and peal.composer is None and \
                        (quick_mode or confirm(f'Possible composer: {composer_name}')):
                    prompt_add_composition_details(composer_name, None, peal, quick_mode)
                else:
                    conductor_bells = [bell for conductor in peal.conductors for bell in conductor.bell_nums]
                    bells, conductor_bells, footnote_str = parse_footnote(line_part, peal.num_bells, conductor_bells)
                    _prompt_add_single_footnote(bells, footnote_str, peal, quick_mode)
    else:
        while True:
            if not confirm(None, confirm_message='Add new footnote?', default=False):
                break
            _prompt_add_single_footnote(None, None, peal, False)


def prompt_add_muffle_type(peal: Peal):
    if peal.muffles is None:
        peal.muffles = choose_option(['None', 'Half-muffled', 'Fully-muffled'],
                                     values=[None, MuffleType.HALF, MuffleType.FULLY],
                                     title='Muffle type',
                                     default=1)


def _prompt_add_single_footnote(bells: list[int],
                                text: str,
                                peal: Peal,
                                quick_mode: bool = False) -> MuffleType:

    ringers = None
    while True:
        if text:
            text = text[0].upper() + text[1:]  # Sentence case the text
            ringers = [peal.get_ringer(bell) for bell in bells] if bells else None
            if not quick_mode:
                print(f'Footnote {len(peal.footnotes) + 1} text:')
                print(f'  > {text}')
            if bells:
                print('Referenced ringer(s):')
                for bell, ringer in zip(bells, ringers):
                    print(f'  - {bell}: {ringer}')
                    if bell < 1 or bell > peal.num_bells:
                        warning(f'Bell referenced in footnote ({bell}) is greater than number of bells ({peal.num_bells})')
                        quick_mode = False
            if quick_mode or confirm(None):
                break
        text, bells = _prompt_footnote_details(bells, text, peal.num_bells, quick_mode)

    if bells:
        for bell, ringer in zip(bells, ringers):
            peal.add_footnote(text, bell, ringer)
    elif len(peal.footnotes) > 0 and \
            peal.footnotes[-1].bell is None and \
            (quick_mode or confirm(None, confirm_message='Add this to previous footnote?', default=True)):
        peal.footnotes[-1].text = peal.footnotes[-1].text + ' ' + text
    else:
        peal.add_footnote(text, None, None)

    muffle_type = None
    if re.match(HALF_MUFFLED_REGEX, text):
        muffle_type = MuffleType.HALF
    elif re.match(MUFFLED_REGEX, text):
        muffle_type = MuffleType.FULLY
    if muffle_type and (quick_mode or confirm(f'Possible {muffle_type.name.lower()}-muffled ringing')):
        peal.muffles = muffle_type


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
    while max_bells:  # Is None if this is a non-peal performance
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
