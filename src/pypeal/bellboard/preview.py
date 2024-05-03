from datetime import date

from pypeal.bellboard.html_generator import HTMLPealGenerator
from pypeal.bellboard.interface import BellboardError
from pypeal.cli.peal_previewer import PealPreviewListener


def get_preview(peal_id: int) -> tuple[str, str, date]:

    generator = HTMLPealGenerator()
    preview_listener = PealPreviewListener()

    try:
        peal_id = generator.download(peal_id)
        generator.parse(preview_listener)

        return preview_listener.text, preview_listener.metadata[0], preview_listener.metadata[1]

    except BellboardError:
        return '[Unable to generate preview]', None, None
