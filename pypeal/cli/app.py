import logging
from typing import Annotated
import typer

from rich import print

import pypeal
from pypeal.bellboard import get_peal as get_bellboard_peal, BellboardPeal, get_id_from_url, get_url_from_id
from pypeal.cli.prompts import choose_option, ask, confirm, panel
from pypeal.peal import Peal
from pypeal.ringer import Ringer
from pypeal.config import set_config_file

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

app = typer.Typer()


@app.command()
def main(
        reset_database: Annotated[bool, typer.Option(help="Reset the database first.")] = False,
        peal_id: Annotated[str, typer.Option("--add-peal", help="Add a peal by Bellboard URL")] = None,
        config: Annotated[str, typer.Option(help="Path to config file.")] = None,
        ):

    if config:
        set_config_file(config)

    initialize_or_exit(reset_database)

    if peal_id:
        logger.debug(f'Adding peal ID {peal_id} provided as "add-peal" option')

    while True:
        peals: dict[str, Peal] = Peal.get_all()
        panel(f'Number of peals: {len(peals)}')

        match choose_option(['Add peal by URL', 'Add random peal', 'Exit'], default=1) if peal_id is None else 1:
            case 1:
                peal_or_url = peal_id
                while True:
                    if peal_or_url:
                        if peal_or_url.isnumeric():
                            peal_id = int(peal_or_url)
                            bb_url = get_url_from_id(peal_or_url)
                        else:
                            bb_url = peal_or_url
                            if not (peal_id := get_id_from_url(peal_or_url)):
                                panel(f'Invalid Bellboard URL or peal ID: {peal_or_url}')
                        if peal_id:
                            break
                    peal_or_url = ask('Bellboard URL or peal ID')

                if peal_id in peals:
                    panel(f'Peal {peal_id} already added')
                else:
                    add_peal(bb_url)
                peal_id = None
            case 2:
                add_peal()
                peal_id = None
            case 3:
                raise typer.Exit()


def add_peal(url: str = None) -> Peal:

    bb_peal: BellboardPeal = get_bellboard_peal(url)

    # Convert basic peal details

    peal = Peal(bellboard_id=bb_peal.id,
                date=bb_peal.date,
                place=bb_peal.place,
                association=bb_peal.association,
                address_dedication=bb_peal.address_dedication,
                county=bb_peal.county,
                changes=bb_peal.changes,
                title=bb_peal.title,
                duration=bb_peal.duration,
                tenor_weight=bb_peal.tenor_weight,
                tenor_tone=bb_peal.tenor_tone)

    # Attempt to match names to ringers

    peal_ringers: list[tuple[Ringer, int, bool]] = []  # Build up list of ringer records and commit at the end (in case of abort)
    bell: int = 1                                      # Track the bell, allowing for multiple bells per ringer
    for bb_ringer in bb_peal.ringers.values():

        matched_ringer: Ringer = None                  # Holds the ringer record that matches the name found on Bellboard

        full_name_match = Ringer.get_by_full_name(bb_ringer.name)
        match len(full_name_match):
            case 0:
                print(f'{bell}: No existing ringers match "{bb_ringer.name}"')
            case 1:
                matched_ringer = prompt_add_ringer(bb_ringer.name, full_name_match[0], bb_ringer.bells)
            case _:
                print(f'{bell}: {len(full_name_match)} existing ringers match "{bb_ringer.name}"')
                matched_ringer = choose_option([f'{r.name} ({r.id})' for r in full_name_match], values=full_name_match, cancel_option='None', return_option=True)

        bb_last_name, bb_given_names = split_full_name(bb_ringer.name)

        while not matched_ringer:
            match choose_option(['Add as new ringer', 'Search alternatives'], default=1, cancel_option='Cancel'):
                case 1:
                    last_name = ask('Last name', default=bb_last_name)
                    given_names = ask('Given name(s)', default=bb_given_names)
                    matched_ringer = Ringer(last_name, given_names)
                case 2:
                    last_name = ask('Last name', default='')
                    given_names = ask('Given name(s)', default='')
                    potential_ringers = Ringer.get_by_name(last_name, given_names)
                    match len(potential_ringers):
                        case 0:
                            print(f'No existing ringers match (given name: "{given_names}", last name: "{last_name}")')
                        case 1:
                            matched_ringer = prompt_add_ringer(bb_ringer.name, potential_ringers[0], bb_ringer.bells)
                        case _:
                            print(f'{len(potential_ringers)} existing ringers match "{(given_names + " " + last_name).strip()}"')
                            matched_ringer = choose_option(potential_ringers, cancel_option='None', return_option=True)
                case None:
                    return None

        if matched_ringer.id is None:
            matched_ringer = Ringer.add(matched_ringer.last_name, matched_ringer.given_names)

        if len(full_name_match) == 0 and \
           f'{bb_given_names} {bb_last_name}' != matched_ringer.name and \
           confirm(f'Add "{bb_given_names} {bb_last_name}" as an alias?'):
            matched_ringer.add_alias(bb_last_name, bb_given_names)

        peal_ringers.append((matched_ringer, bb_ringer.bells, bb_ringer.is_conductor))
        bell += len(bb_ringer.bells)

    # Commit data

    peal = Peal.add(peal)
    for pr in peal_ringers:
        peal.add_ringer(*pr)

    for bb_footnote in bb_peal.footnotes:
        peal.add_footnote(bb_footnote)

    # Confirm

    panel(str(peal), title=peal.bellboard_url)
    if confirm('Save this peal?'):
        print(f'Peal {peal.bellboard_id} added')
        return peal
    else:
        return None


def prompt_add_ringer(name: str, ringer: Ringer, bell: int) -> Ringer:
    if confirm(f'{bell}: "{name}" -> {ringer}', confirm_message='Is this the correct ringer?', default=True):
        return ringer
    return None


def split_full_name(full_name: str) -> tuple[str, str]:
    last_name = full_name.split(' ')[-1]
    given_names = ' '.join(full_name.split(' ')[:-1])
    return last_name, given_names


def initialize_or_exit(reset_db: bool = False):
    if not pypeal.initialize(reset_db):
        panel('Unable to connect to pypeal database')
        raise typer.Exit()
