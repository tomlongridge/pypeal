import csv
from datetime import datetime
import os
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.peal_previewer import PealPreviewListener
from pypeal.cli.peal_prompter import PealPromptListener
from pypeal.cli.prompt_add_tower import prompt_find_tower
from pypeal.cli.prompt_deduplicate_peal import prompt_bellboard_duplicate, prompt_database_duplicate
from pypeal.cli.prompts import UserCancelled, confirm, panel, warning
from pypeal.entities.method import Stage
from pypeal.entities.peal import BellType, Peal

from pypeal.entities.tower import Ring, Tower


class CSVImportError(Exception):
    pass


def import_peal_csv(data_file_path: str):

    preview_listener = PealPreviewListener()
    quick_mode_listener = PealPromptListener()
    quick_mode_listener.quick_mode = True
    prompt_listener = PealPromptListener()

    while True:

        with open(data_file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.read().splitlines()

        # End processing if it's just the headers left
        if len(lines) == 1:
            break

        config_import_name = os.path.basename(data_file_path).replace('.csv', '').replace('_', ' ').title()
        config_date_format = '%Y/%m/%d'
        config_append_stage_name = False
        header_lines = []
        body_lines = []
        for line in lines:
            if line.startswith('#'):
                metadata = line[1:].strip()
                if metadata.startswith('name='):
                    config_import_name = metadata[5:]
                elif metadata.startswith('date_format='):
                    config_date_format = metadata[12:]
                elif metadata.startswith('append_stage_name='):
                    config_append_stage_name = metadata[18:].lower() in ['true', 'yes', '1']
                header_lines.append(line)
            else:
                body_lines.append(line)

        line_index = 0
        for peal_data in csv.DictReader(body_lines):

            line_index += 1

            if 'Reference' not in peal_data:
                row_id = f'{config_import_name} L{line_index}'
            else:
                row_id = f'{config_import_name} ID {peal_data["Reference"]}'

            print(f'Importing peal {row_id}...')

            _read_peal_line(preview_listener, peal_data, None, config_date_format, config_append_stage_name)

            panel(preview_listener.text, title='Preview', width=100)

            basic_peal = _generate_basic_peal(peal_data, config_date_format)
            if prompt_database_duplicate(basic_peal) is not None \
                    and prompt_bellboard_duplicate(basic_peal) is not None \
                    and not confirm(None, confirm_message='Continue adding new peal?'):
                return

            for listener in [quick_mode_listener, prompt_listener]:

                try:
                    _read_peal_line(listener, peal_data, basic_peal.ring, config_date_format, config_append_stage_name)

                    panel(str(listener.peal), title='Final', width=100)

                    if confirm(None):
                        new_peal = listener.peal
                        break

                except UserCancelled:
                    try:
                        if listener.quick_mode and confirm(None, confirm_message='Continue in prompt mode?'):
                            continue
                        print(f'Aborting peal #{line_index}')
                        if confirm(None, 'Exit?'):
                            return
                    except UserCancelled:
                        return

            # If we've created the peal, commit it and remove the row from the CSV file
            if new_peal:
                new_peal.external_reference = row_id
                new_peal.commit()
                with open(data_file_path, 'w', encoding='utf-8-sig') as fw:
                    fw.write('\n'.join(header_lines))
                    fw.write('\n')
                    fw.write('\n'.join(body_lines[:line_index]))
                    fw.write('\n')
                    fw.write('\n'.join(body_lines[line_index+1:]))
                break  # Break out to the outer while loop so we re-read the file


def _read_bell_type(data: dict) -> BellType:
    if 'Bell Type' in data:
        match data['Bell Type'].lower():
            case 'hand':
                return BellType.HANDBELLS
            case 'tower':
                return BellType.TOWER
    return BellType.TOWER


def _read_date(data: dict, date_format: str) -> datetime.date:
    if 'Date' not in data:
        raise CSVImportError('Date not found in data')
    try:
        return datetime.date(datetime.strptime(data['Date'], date_format))
    except ValueError:
        raise CSVImportError(f'Unable to parse date: {data["Date"]} in format {date_format}')


def _read_peal_line(listener: PealGeneratorListener, data: dict, place: Ring | None, date_format: str, append_stage_name: bool):

    listener.new_peal(None)
    listener.bell_type(_read_bell_type(data))

    if place is not None:
        listener.tower(dove_id=place.tower.dove_id)
    else:
        listener.location(data.get('Dedication', None), data['Place'], data.get('County', None), data.get('Country', None))

    num_ringers = 0
    while True:
        ringer_data = data.get(f'Ringer {num_ringers + 1}', None)
        if ringer_data is None or ringer_data == '':
            break
        num_ringers += 1
    if num_ringers == 0:
        raise CSVImportError('No ringers found')

    if 'Date' in data:
        listener.date(_read_date(data, date_format))
    if 'Association' in data:
        listener.association(data['Association'])
    if 'Changes' in data and data['Changes'].isnumeric():
        listener.changes(int(data['Changes']))
    if 'Title' in data:
        if append_stage_name:
            if 'Stage' in data:
                stage = data['Stage']
                if data['Stage'].isnumeric():
                    stage = str(Stage(int(data['Stage'])))
            else:
                warning(f'Stage not found for peal {data["Title"]}, using number of ringers ({num_ringers}) but it might have tenor cover')
                stage = str(Stage(num_ringers))
            listener.title(f'{data["Title"]} {stage}')
        else:
            listener.title(data['Title'])
    if 'Duration' in data:
        listener.duration(data['Duration'])

    ringer_num = 0
    while True:

        ringer_num += 1
        ringer_data = data.get(f'Ringer {ringer_num}', None)
        if ringer_data is None or ringer_data == '':
            break

        is_conductor = False
        if ringer_data.lower().endswith('(c)'):
            is_conductor = True
            ringer_data = ringer_data[:-4].strip()

        listener.ringer(ringer_data, [ringer_num], None, is_conductor)

    if 'Footnote' in data:
        listener.footnote(data['Footnote'])

    listener.end_peal()


def _generate_basic_peal(data: dict, date_format: str) -> Peal:
    peal = Peal()
    peal.bell_type = _read_bell_type(data)
    peal.date = _read_date(data, date_format)

    tower = None
    if 'Place' in data and data['Place'] is not None:
        tower_matches = Tower.search(place=data['Place'], exact_match=False)
        if len(tower_matches) == 1:
            tower = tower_matches[0]
    if 'TowerID' in data and data['TowerID'] is not None:
        if data['TowerID'].isnumeric():
            tower = prompt_find_tower(int(data['TowerID']))
        else:
            raise CSVImportError(f'Invalid TowerID: {data["TowerID"]}')
    if not tower and confirm(None, 'Attempt to find a tower?', default=True):
        tower = prompt_find_tower(data.get('Place', None))
    if tower:
        peal.ring = tower.get_active_ring(peal.date)
    else:
        peal.place = data.get('Place', None)
        peal.dedication = data.get('Dedication', None)
        peal.county = data.get('County', None)
        peal.country = data.get('Country', None)
    return peal
