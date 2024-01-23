import logging

from pypeal.bellboard.interface import BellboardError, get_url_from_id
from pypeal.bellboard.html_generator import HTMLPealGenerator
from pypeal.cli.generator import PealGenerator
from pypeal.cli.peal_prompter import PealPromptListener
from pypeal.cli.peal_previewer import PealPreviewListener
from pypeal.cli.prompt_commit_peal import prompt_commit_peal
from pypeal.cli.prompts import UserCancelled, confirm, panel, error
from pypeal.peal import Peal

logger = logging.getLogger('pypeal')


def prompt_import_peal(peal_id: int = None) -> Peal:

    generator = HTMLPealGenerator()
    preview_listener = PealPreviewListener()

    try:
        peal_id = generator.download(peal_id)
        generator.parse(preview_listener)
        panel(preview_listener.text, title=get_url_from_id(peal_id))

        if Peal.get(bellboard_id=peal_id) and \
                not confirm(f'Peal {peal_id} already added to database', confirm_message='Overwrite?', default=False):
            return

        return add_peal(generator)

    except BellboardError as e:
        logger.exception('Error getting peal from Bellboard: %s', e)
        error(e)


def add_peal(generator: PealGenerator) -> Peal:

    prompt_listener = PealPromptListener()
    prompt_listener.quick_mode = confirm(None, confirm_message='Try for a quick-add?', default=True)

    peal: Peal = None
    while True:

        try:
            generator.parse(prompt_listener)
        except UserCancelled:
            if confirm(None, confirm_message='Retry entire peal?', default=True):
                prompt_listener.quick_mode = False
                continue

        peal = prompt_listener.peal

        saved_peal = prompt_commit_peal(peal)
        if saved_peal:
            break
        elif prompt_listener.quick_mode and \
                confirm(None, confirm_message='Try again in prompt mode?', default=True):
            prompt_listener.quick_mode = False
            continue
        else:
            break

    return saved_peal
