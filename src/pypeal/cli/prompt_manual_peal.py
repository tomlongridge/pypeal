from pypeal.cli.manual_generator import ManualGenerator
from pypeal.cli.prompt_import_peal import prompt_add_peal
from pypeal.cli.prompt_submit import prompt_submit_peal
from pypeal.cli.prompts import confirm, heading


def prompt_manual_peal():
    heading('Add peal manually')
    new_peal = prompt_add_peal(ManualGenerator())
    if confirm(None, confirm_message='Submit peal to BellBoard?', default=True):
        prompt_submit_peal(new_peal)
