import logging
from typing import Annotated
import typer

from rich import print
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt

import pypeal
import pypeal.bellboard
from pypeal.peal import Peal

app = typer.Typer()

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


@app.command()
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

        print('Options: 1) Add peal by URL, 2) Add random peal, 3) Exit')
        match IntPrompt.ask('Select action'):
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
    peal = pypeal.add_peal(id)
    print(f'Peal {peal.bellboard_id} added')
    print(Panel(str(peal), title=peal.bellboard_url))
    return peal


def initialize_or_exit(reset_db: bool = False):
    if not pypeal.initialize(reset_db):
        print(Panel('Unable to connect to pypeal database', title='pypeal'))
        raise typer.Exit()


if __name__ == "__main__":
    app()
