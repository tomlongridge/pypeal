import logging

from pypeal.bellboard.interface import BellboardError
from pypeal.bellboard.utils import get_url_from_id
from pypeal.bellboard.html_generator import HTMLPealGenerator
from pypeal.cli.chooser import choose_option
from pypeal.cli.generator import PealGenerator
from pypeal.cli.peal_prompter import PealPromptListener
from pypeal.cli.peal_previewer import PealPreviewListener
from pypeal.cli.prompt_commit_peal import prompt_commit_peal
from pypeal.cli.prompts import UserCancelled, confirm, heading, panel, error
from pypeal.entities.peal import Peal

logger = logging.getLogger('pypeal')


def prompt_import_peal(peal_id: int = None) -> Peal:

    heading('Import peal from BellBoard')

    generator = HTMLPealGenerator()
    preview_listener = PealPreviewListener()

    try:
        peal_id = generator.download(peal_id)
        generator.parse(preview_listener)
        panel(preview_listener.text, title=get_url_from_id(peal_id))

        if Peal.get(bellboard_id=peal_id) and \
                not confirm(f'Peal {peal_id} already added to database', confirm_message='Overwrite?', default=False):
            return

        return prompt_add_peal(generator)

    except BellboardError as e:
        logger.exception('Error getting peal from Bellboard: %s', e)
        error(e)


def prompt_add_peal(generator: PealGenerator) -> Peal:

    prompt_listener: PealPromptListener = None
    saved_peal: Peal = None
    while True:

        prompt_choice = choose_option(['Quick mode', 'Amend footnote only', 'Prompt mode'],
                                      title='Retry entire peal?' if prompt_listener else 'Try for quick-add?',
                                      none_option='Cancel' if prompt_listener else None,
                                      default=1 if not prompt_listener else 3 if prompt_listener.quick_mode else None)

        if not prompt_listener:
            prompt_listener = PealPromptListener()

        match prompt_choice:
            case 1:
                prompt_listener.set_quick_mode(True)
            case 2:
                prompt_listener.set_quick_mode(amend_footnote=True)
            case 3:
                prompt_listener.set_quick_mode(False)
            case None:
                break

        try:
            generator.parse(prompt_listener)
            if saved_peal := prompt_commit_peal(prompt_listener.peal):
                break
        except UserCancelled:
            print('Peal import aborted')

    return saved_peal
