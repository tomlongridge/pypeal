from pypeal.cli.chooser import choose_option
from pypeal.cli.prompts import ask_int, confirm, panel, prompt_peal_id
from pypeal.peal import Peal


def prompt_delete_peal(peal_id_or_url: str = None):
    peal: Peal
    match choose_option(['Bellboard ID/URL', 'Peal ID'], default=1) if not peal_id_or_url else 1:
        case 1:
            peal_id = prompt_peal_id(peal_id_or_url)
            peal = Peal.get(bellboard_id=peal_id)
        case 2:
            peal_id = ask_int('Peal ID', min=1, required=True)
            peal = Peal.get(id=peal_id)
    panel(str(peal))
    if confirm(None, 'Delete peal?'):
        peal.delete()
