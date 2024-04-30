from pypeal.cli.prompt_peal_input import prompt_peal_by_id
from pypeal.cli.prompt_submit import prompt_submit_peal
from pypeal.cli.prompts import confirm, heading, panel, press_any_key


def prompt_view_peal(peal_id_or_url: str = None):
    heading('View peal')
    for peal in prompt_peal_by_id(peal_id_or_url, ask_for_database_id=True):
        panel(peal)
        if peal.bellboard_id is None:
            if confirm('This peal is not associated with a performance on BellBoard', confirm_message='Submit peal?', default=True):
                prompt_submit_peal(peal)
        else:
            press_any_key()
