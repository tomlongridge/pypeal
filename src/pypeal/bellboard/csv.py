import csv
from datetime import datetime
from pypeal.bellboard.utils import get_url_from_id
from pypeal.bellboard.search import search as bb_search
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.generator import PealGenerator
from pypeal.cli.peal_previewer import PealPreviewListener
from pypeal.cli.peal_prompter import PealPromptListener
from pypeal.cli.prompts import confirm, panel, warning
from pypeal.entities.peal import BellType, Peal
from rich.console import Console


class CSVPealGenerator(PealGenerator):

    def __init__(self,
                 encoding: str = 'utf-8-sig',
                 date_format: str = '%d/%m/%Y') -> None:
        super().__init__()
        self.encoding = encoding
        self.date_format = date_format

    def parse(self, data_file_path: str):

        console = Console()
        preview_listener = PealPreviewListener()
        quick_mode_listener = PealPromptListener()
        quick_mode_listener.quick_mode = True
        prompt_listener = PealPromptListener()

        while True:

            with open(data_file_path, 'r', encoding=self.encoding) as f:
                lines = f.read().splitlines()

            # End processing if it's just the headers left
            if len(lines) == 1:
                break

            line_index = 0
            for peal in csv.DictReader(lines):

                line_index += 1

                if next(iter(peal.values())).startswith('#'):
                    continue

                self._read_peal_line_initial(preview_listener, peal)
                self._read_peal_line_final(preview_listener, peal)

                preview_panel = panel(preview_listener.text, title='Preview', width=100)
                console.print(preview_panel)

                for listener in [quick_mode_listener, prompt_listener]:

                    try:
                        self._read_peal_line_initial(listener, peal)

                        if listener.peal.ring is not None:
                            self._dedup_peal(listener.peal)

                        self._read_peal_line_final(listener, peal)

                        # Link to BellBoard ID if there is one found
                        if bellboard_id:
                            listener.peal.bellboard_id = bellboard_id

                        final_panel = Panel(str(listener.peal), title='Final', width=100)
                        console.print(Columns([preview_panel, final_panel]))

                        if confirm(None):
                            new_peal = listener.peal
                            break

                    except UserCancelled:
                        try:
                            if listener.quick_mode and confirm(None, confirm_message='Continue in prompt mode?'):
                                continue
                            print(f'Aborting peal {peal["qp_id"]}')
                            if confirm(None, 'Exit?'):
                                exit()
                        except UserCancelled:
                            exit()

                # If we've created the peal, commit it and remove the row from the CSV file
                if new_peal:
                    new_peal.external_reference = f'Bathwick Tower DB ID {peal["qp_id"]}'
                    new_peal.commit()
                    with open('QP.csv', 'w', encoding='utf-8-sig') as fw:
                        fw.write('\n'.join(lines[:line_index]))
                        fw.write('\n')
                        fw.write('\n'.join(lines[line_index+1:]))
                    break  # Break out to the outer while loop so we re-read the file

    def _read_peal_line_initial(self, listener: PealGeneratorListener, data: dict):

        listener.new_peal(None)
        if 'Bell Type' in data:
            match data['Bell Type'].lower():
                case 'hand':
                    listener.bell_type(BellType.HANDBELLS)
                case 'tower', _:
                    listener.bell_type(BellType.TOWER)
        if 'Place' in data:
            listener.location(place=data['Place'])
        if 'Date' in data:
            date_rung = datetime.date(datetime.strptime(data['Date'], self.date_format))
            listener.date(date_rung)

    def _read_peal_line_final(self, listener: PealGeneratorListener, data: dict):

        if 'Association' in data:
            listener.association(data['Association'])
        if 'Changes' in data and data['Changes'].isnumeric():
            listener.changes(int(data['Changes']))
        if 'Title' in data:
            listener.title(data['Title'])
        if 'Duration' in data:
            listener.duration(data['Duration'])

        ringer_num = 1
        while True:

            ringer_data = data.get(f'Ringer {ringer_num}', None)
            if ringer_data is None:
                break

            is_conductor = False
            if ringer_data.lower().endswith('(c)'):
                is_conductor = True
                ringer_data = ringer_data[:-4].strip()

            listener.ringer(ringer_data, [ringer_num], None, is_conductor)

        if 'Footnote' in data:
            listener.footnote(data['footnote'])

        listener.end_peal()

    def _dedup_peal(self, peal: Peal):

        # Check database for peals the same day and tower in database
        for existing_peal in Peal.search(tower_id=peal.ring.tower, date_from=peal.date, date_to=peal.date):
            print(f'Existing peal in database: {existing_peal.id}')
            warning(str(existing_peal))
            if not confirm(None, confirm_message='Continue adding new peal?'):
                return False

        # Check database for peals the same day and tower on BellBoard
        for existing_peal_id in bb_search(tower_id=peal.ring.tower, date_from=peal.date, date_to=peal.date):
            print(f'Existing peal on BellBoard: {get_url_from_id(existing_peal_id)}')
            warning(str(existing_peal))
            if not confirm(None, confirm_message='Import?'):
            if not confirm(None, confirm_message='Continue adding new peal?'):
                return False

        return True
