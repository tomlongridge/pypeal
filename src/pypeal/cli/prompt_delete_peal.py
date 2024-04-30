from pypeal.cli.prompt_peal_input import prompt_peal_by_id
from pypeal.cli.prompts import confirm, heading, panel


def prompt_delete_peal(peal_id_or_url: str = None):
    heading('Delete peal')
    for peal in prompt_peal_by_id(peal_id_or_url, ask_for_database_id=True):
        panel(peal)
        if confirm(None, 'Delete peal?'):
            peal.delete()
