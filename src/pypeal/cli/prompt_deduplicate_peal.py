from datetime import date
from pypeal.bellboard.preview import get_preview
from pypeal.bellboard.utils import get_url_from_id
from pypeal.cli.prompts import confirm, make_peal_panel, panel, warning
from pypeal.entities.peal import Peal
from pypeal.bellboard.search import find_matching_peal
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.markup import escape


def prompt_database_duplicate(peal: Peal, preview: str = None) -> Peal:

    if peal.bellboard_id and (existing_peal := Peal.get(bellboard_id=peal.bellboard_id)):
        panel(str(existing_peal), width=80)
        warning(f'Peal with BellBoard ID {peal.bellboard_id} already exists in database')
        return existing_peal

    # Check for existing peal with the same basic details
    if existing_peals := Peal.search(date_from=peal.date or None,
                                     date_to=peal.date or None,
                                     tower_id=peal.ring.tower.id if peal.ring else None,
                                     place=peal.place if not peal.ring else None,
                                     bell_type=peal.bell_type or None,
                                     length_type=peal.length_type or None):
        if len(existing_peals) == 1:
            warning('Found a possible duplicate peal in the database')
        else:
            warning(f'{len(existing_peals)} possible duplicate peals found in the database')
            if not confirm(None, confirm_message='Check these peals for duplicates?'):
                return None

        console = Console()
        for existing_peal in existing_peals:
            console.print(Columns([make_peal_panel(preview or peal),
                                   make_peal_panel(existing_peal)]))
            if not preview and confirm(None, confirm_message='See differences?'):
                diffs = ''
                for field, (left, right) in existing_peal.diff(peal).items():
                    diffs += f'{field}: {left} -> {right}\n'
                panel(diffs.strip(), title='Differences')
            if confirm(None, confirm_message='Is this the same peal?'):
                return existing_peal

    return None


def prompt_bellboard_duplicate(peal: Peal, preview: str = None, bb_peal_ids: list[int] = None) -> tuple[int, str, date]:

    console = Console()
    first_peal = True
    for bb_peal_id, search_url in find_matching_peal(peal) if bb_peal_ids is None else bb_peal_ids:
        if first_peal:
            warning(f'Possible duplicate peals found on BellBoard: {search_url}')
            if not confirm(None, confirm_message='Check these peals for duplicates?'):
                return None

        preview_str, submitter, date_submitted = get_preview(bb_peal_id)
        console.print(Columns([Panel(escape(str(peal) if preview is None else preview)),
                               Panel(escape(preview_str))],
                              expand=True,
                              equal=True))

        if confirm(get_url_from_id(bb_peal_id), confirm_message='Is this the same peal?'):
            return bb_peal_id, submitter, date_submitted

        first_peal = False

    return None
