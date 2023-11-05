from pypeal.cli.prompts import ask, confirm
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

            bells, footnote = parse_footnote(line_part)

            while True:
                if footnote.strip('. ') != text.strip('. '):
                    ringers = [peal.get_ringer(bell) for bell in bells] if bells else None
                    print(f'Footnote {len(peal.footnotes) + 1} text:')
                    print(f'  > {footnote}')
                    if bells:
                        print('Referenced ringer(s):')
                        for bell, ringer in zip(bells, ringers):
                            print(f'  - {bell}: {ringer}')
                if confirm(None):
                    if bells:
                        for bell, ringer in zip(bells, ringers):
                            peal.add_footnote(footnote, bell, ringer)
                    else:
                        peal.add_footnote(footnote, None, None)
                    break
                else:
                    footnote = ask('Footnote text', default=footnote)
                    bells = ask('Bells (comma-separated)', default=','.join(bells) if bells else None)
