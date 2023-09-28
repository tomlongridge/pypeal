import logging
from typing import Annotated
import typer

from rich import print
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

import pypeal
from pypeal.bellboard import get_peal as get_bellboard_peal, BellboardPeal
from pypeal.cli.prompts import option_prompt
from pypeal.peal import Peal
from pypeal.ringer import Ringer

logger = logging.getLogger('pypeal')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

runner = typer.Typer()


@runner.command()
def main(
        reset_database: Annotated[bool, typer.Option(help="Reset the database first.")] = False,
        add: Annotated[str, typer.Option(help="Add a peal by Bellboard URL")] = None
        ):

    initialize_or_exit(reset_database)

    if add:
        if (peal_id := pypeal.bellboard.get_id_from_url(add)):
            add_peal(peal_id)
        else:
            print(Panel(f'Invalid Bellboard URL {add}', title='pypeal'))

    while True:
        peals: dict[str, Peal] = pypeal.get_peals()
        print(Panel(f'Number of peals: {len(peals)}', title='pypeal'))

        match option_prompt(['Add peal by URL', 'Add random peal', 'Exit'], default=1):
            case 1:
                peal_id = None
                while not peal_id:
                    url = Prompt.ask('Bellboard URL')
                    if not (peal_id := pypeal.bellboard.get_id_from_url(url)):
                        print(Panel(f'Invalid Bellboard URL {url}', title='pypeal'))

                if peal_id in peals:
                    print(Panel(f'Peal {peal_id} already added', title='pypeal'))
                else:
                    add_peal(peal_id)
            case 2:
                add_peal()
            case 3:
                raise typer.Exit()


def add_peal(id: int = None) -> Peal:

    bb_peal: BellboardPeal = get_bellboard_peal(id)

    peal = Peal.add(
        Peal(
            bellboard_id=bb_peal.id,
            date=bb_peal.date,
            place=bb_peal.place,
            association=bb_peal.association,
            address_dedication=bb_peal.address_dedication,
            county=bb_peal.county,
            changes=bb_peal.changes,
            title=bb_peal.title,
            duration=bb_peal.duration,
            tenor_weight=bb_peal.tenor_weight,
            tenor_tone=bb_peal.tenor_tone))

    for bell, bb_ringer in enumerate(bb_peal.ringers.values(), start=1):
        matched_ringer = None
        full_name_match = Ringer.get_by_full_name(bb_ringer.name)
        match len(full_name_match):
            case 0:
                print(f'{bell}: No existing ringers match "{bb_ringer.name}"')
            case 1:
                matched_ringer = prompt_add_ringer(full_name_match[0], bb_ringer.bells)
            case _:
                print(f'{bell}: {len(full_name_match)} existing ringers match "{bb_ringer.name}"')

        while not matched_ringer:
            match option_prompt(['Add as new ringer', 'Search alternatives'], default=1):
                case 1:
                    last_name = bb_ringer.name.split(' ')[-1]
                    given_names = ' '.join(bb_ringer.name.split(' ')[:-1])
                    matched_ringer = Ringer.add(last_name, given_names)
                case 2:
                    last_name = Prompt.ask('Last name')
                    given_names = Prompt.ask('Given name(s)')
                    potential_ringers = Ringer.get_by_name(last_name, given_names)
                    match len(potential_ringers):
                        case 0:
                            print(f'No existing ringers match "{given_names} {last_name}"')
                        case 1:
                            matched_ringer = prompt_add_ringer(potential_ringers[0], bb_ringer.bells)
                        case _:
                            print(f'{len(potential_ringers)} existing ringers match "{given_names} {last_name}"')
                            matched_ringer = option_prompt(potential_ringers, cancel_option='None', return_option=True)

        peal.add_ringer(matched_ringer, bb_ringer.bells, bb_ringer.is_conductor)

    for bb_footnote in bb_peal.footnotes:
        peal.add_footnote(bb_footnote)

    print(f'Peal {peal.bellboard_id} added')
    print(Panel(str(peal), title=peal.bellboard_url))
    return peal


def prompt_add_ringer(ringer: Ringer, bell: int) -> Ringer:
    print(f'{bell}: {ringer}')
    if Confirm.ask('Is this the correct ringer?', default='y'):
        return ringer
    return None


def initialize_or_exit(reset_db: bool = False):
    if not pypeal.initialize(reset_db):
        print(Panel('Unable to connect to pypeal database', title='pypeal'))
        raise typer.Exit()
