import csv
from datetime import datetime
import os
import re
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.chooser import choose_option
from pypeal.cli.prompt_commit_peal import prompt_commit_peal
from pypeal.cli.peal_previewer import PealPreviewListener
from pypeal.cli.peal_prompter import PealPromptListener
from pypeal.cli.prompt_add_tower import prompt_find_tower
from pypeal.cli.prompt_deduplicate_peal import prompt_bellboard_duplicate, prompt_database_duplicate
from pypeal.cli.prompt_import_peal import prompt_import_peal
from pypeal.cli.prompts import UserCancelled, confirm, error, panel, warning
from pypeal.entities.method import Stage
from pypeal.entities.peal import BellType, Peal

from pypeal.entities.tower import Tower


class CSVImportError(Exception):
    pass


def prompt_csv_import(data_file_path: str):

    if not os.path.exists(data_file_path):
        error(f'Unable to import peals from {data_file_path}')
        return

    print(f'Importing peals from {data_file_path}...')

    preview_listener = PealPreviewListener()
    quick_mode_listener = PealPromptListener()
    quick_mode_listener.set_quick_mode()
    prompt_listener = PealPromptListener()

    while True:

        with open(data_file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.read().splitlines()

        config_import_name = os.path.basename(data_file_path).replace('.csv', '').replace('_', ' ').title()
        config_date_format = '%Y/%m/%d'
        header_lines = []
        body_lines = []
        num_data_lines = 0
        for line in lines:
            if line.startswith('#') and len(body_lines) == 0:  # Once a body line has been found, commented lines are peals
                metadata = line[1:].strip()
                if metadata.startswith('name='):
                    config_import_name = metadata[5:]
                elif metadata.startswith('date_format='):
                    config_date_format = metadata[12:]
                else:
                    warning(f'Unknown config line in CSV file: {metadata}')
                header_lines.append(line)
            else:
                body_lines.append(line)
                num_data_lines += 1 if line.strip() != '' and line[0] != '#' else 0

        # End processing if just the column headers are found
        if num_data_lines == 1:
            break

        line_index = 0
        for peal_data in csv.DictReader(body_lines):

            line_index += 1
            file_line_index = line_index + len(header_lines) + 1

            if list(peal_data.values())[0].strip() == '' or \
                    list(peal_data.values())[0][0] == '#':  # Skip empty lines and comments
                continue

            if 'Reference' not in peal_data:
                row_id = f'{config_import_name} L{file_line_index}'
            else:
                row_id = f'{config_import_name} ID {peal_data["Reference"]}'

            print(f'Importing peal {row_id}...')
            saved_peal = None
            try:
                _read_peal_line(preview_listener, peal_data, None, config_date_format)
                panel(preview_listener.text, title='Preview', width=100)
                basic_peal = _generate_basic_peal(peal_data, config_date_format)

                if prompt_database_duplicate(basic_peal, preview_listener.text) is not None:
                    print(f'Peal {row_id} already exists in database')
                elif bb_data := prompt_bellboard_duplicate(basic_peal, preview=preview_listener.text):
                    if existing_peal := Peal.get(bellboard_id=bb_data[0]):
                        panel(existing_peal)
                        print(f'Peal {row_id} exists on BellBoard ({bb_data[0]}) and already exists in database ({existing_peal.id})')
                    elif confirm(f'Peal {row_id} exists on BellBoard ({bb_data[0]}) but has not been imported to the database',
                                 confirm_message='Import?',
                                 default=True):
                        saved_peal = prompt_import_peal(bb_data[0])
                else:

                    prompt_listener = PealPromptListener()
                    prompt_mode = choose_option(['Quick mode', 'Amend footnote only', 'Prompt mode'], title='Try for a quick-add?', default=1)
                    if prompt_mode != 3:
                        prompt_listener.set_quick_mode(amend_footnote=prompt_mode == 2)

                    while True:

                        try:
                            _read_peal_line(prompt_listener, peal_data, basic_peal, config_date_format)
                        except UserCancelled:
                            if confirm(None, confirm_message='Retry entire peal?', default=True):
                                prompt_listener.quick_mode = False
                                continue

                        prompt_listener.peal.external_reference = row_id
                        saved_peal = prompt_commit_peal(prompt_listener.peal)
                        if not saved_peal and \
                                prompt_listener.quick_mode and \
                                confirm(None, confirm_message='Try again in prompt mode?', default=True):
                            prompt_listener.quick_mode = False
                            continue
                        else:
                            break

            except CSVImportError as e:
                error(f'Error importing peal {file_line_index}: {e}')

            except UserCancelled:
                print(f'Aborting CSV import at line {file_line_index}')
                return

            if not saved_peal:
                print(f'Aborting peal {file_line_index}')

            # Comment-out the current line and break out to re-read the file
            with open(data_file_path, 'w', encoding='utf-8-sig') as fw:
                if header_lines:
                    fw.write('\n'.join(header_lines))
                    fw.write('\n')
                fw.write('\n'.join(body_lines[:line_index]))
                fw.write('\n')
                fw.write(f'# {body_lines[line_index]}')
                fw.write('\n')
                fw.write('\n'.join(body_lines[line_index+1:]))
            break


def _read_bell_type(data: dict) -> BellType:
    if 'Bell Type' in data:
        match data['Bell Type'].lower():
            case 'hand':
                return BellType.HANDBELLS
            case 'tower':
                return BellType.TOWER
    return None


def _read_date(data: dict, date_format: str) -> datetime.date:
    if 'Date' not in data:
        raise CSVImportError('Date not found in peal data')
    try:
        return datetime.date(datetime.strptime(data['Date'], date_format))
    except ValueError:
        raise CSVImportError(f'Unable to parse date: {data["Date"]} in format {date_format}')


def _read_peal_line(listener: PealGeneratorListener, data: dict, basic_peal: Peal | None, date_format: str):

    listener.new_peal(None)

    bell_type = _read_bell_type(data)
    listener.bell_type(bell_type)
    listener.date(_read_date(data, date_format))

    if basic_peal is not None:
        if basic_peal.ring is not None:
            listener.tower(dove_id=basic_peal.ring.tower.dove_id)
        elif basic_peal.place is not None:
            listener.location(basic_peal.dedication, basic_peal.place, basic_peal.county, basic_peal.country)
    elif 'Place' in data:
        if data['Place'].isnumeric() and bell_type != BellType.HANDBELLS and (tower := Tower.get(dove_id=int(data['Place']))):
            listener.location(tower.dedication,
                              tower.place + (f' ({tower.sub_place})' if tower.sub_place else ''),
                              tower.county,
                              tower.country)
        else:
            listener.location(data.get('Dedication', None), data['Place'], data.get('County', None), data.get('Country', None))
    else:
        raise CSVImportError('No Place found in peal data')

    ringer_column = 0
    num_ringers = 0
    while True:
        ringer_column += 1
        ringer_data = data.get(f'Ringer {ringer_column}', None)
        if ringer_data is None:
            break
        elif ringer_data != '':
            num_ringers += 1
    if num_ringers == 0:
        raise CSVImportError('No ringers found in peal data')

    if 'Association' in data:
        listener.association(data['Association'])
    if 'Changes' in data and data['Changes'].isnumeric():
        listener.changes(int(data['Changes']))
    if 'Title' in data:
        if 'Stage' in data:
            stage = data['Stage']
            if data['Stage'].isnumeric():
                stage = str(Stage(int(data['Stage'])))
            else:
                stage = Stage.from_method(data['Stage'])
        elif Stage.from_method(data['Title']):
            # The stage is already in the title
            stage = None
        elif data['Title'].split(' ')[0].isnumeric():
            stage = data['Title'].split(' ')[0]
        else:
            warning(f'Stage not found for peal {data["Title"]}, using number of ringers ({num_ringers}) but it might have tenor cover.')
            stage = str(Stage(num_ringers))
        listener.title(data["Title"] + (f' {stage}' if stage else ''))
    else:
        raise CSVImportError('No Title found in peal data')
    if 'Duration' in data:
        listener.duration(data['Duration'])

    ringer_column = 0
    ringer_num = 0
    bell_num = 0
    ringer_data = None
    while True:

        ringer_column += 1
        ringer_data_str = data.get(f'Ringer {ringer_column}', None)
        if ringer_data_str is None:
            break
        else:
            bell_num += 1
            if ringer_data_str == '':
                continue
            else:
                ringer_num += 1

        is_conductor = False
        if ringer_data_str.lower().endswith('(c)'):
            is_conductor = True
            ringer_name = ringer_data_str[:-3].strip()
        else:
            ringer_name = ringer_data_str

        if ringer_data is not None:
            if ringer_data[0].lower() == ringer_name.lower():
                ringer_data = (ringer_name,
                               [*ringer_data[1], ringer_num],
                               [*ringer_data[2], bell_num],
                               ringer_data[3] or is_conductor)
            else:
                listener.ringer(*ringer_data)
                ringer_data = (ringer_name, [ringer_num], [bell_num], is_conductor)
        else:
            ringer_data = (ringer_name, [ringer_num], [bell_num], is_conductor)

    listener.ringer(*ringer_data)

    if 'Footnote' in data:
        listener.footnote(data['Footnote'])

    listener.end_peal()


def _generate_basic_peal(data: dict, date_format: str) -> Peal:
    peal = Peal()
    peal.bell_type = _read_bell_type(data)
    peal.date = _read_date(data, date_format)

    place = data['Place'].strip()
    tower = None
    if place.isnumeric():
        tower = Tower.get(dove_id=int(place))
        if not tower:
            raise CSVImportError(f'Tower with Dove ID {data["Place"]} not found')
    else:
        tower_matches = Tower.search(place=place, exact_match=False)
        if len(tower_matches) == 1:
            tower = tower_matches[0]
    if not tower and peal.bell_type != BellType.HANDBELLS and confirm(None, 'Attempt to find a tower?', default=True):
        tower = prompt_find_tower(data.get('Place', None))
    if tower:
        peal.ring = tower.get_active_ring(peal.date)
    else:
        dedication = None
        if place_match := re.match(r'(?P<place>.*?)\((?P<dedication>.*?)\)$', place):
            place_data = place_match.groupdict()
            place = place_data['place'].strip()
            dedication = place_data['dedication']
        elif ',' in place:
            place_parts = place.split(', ')
            place = place_parts[0]
            dedication = ', '.join(place_parts[1:])
        peal.place = place
        peal.dedication = dedication or data.get('Dedication', None)
        peal.county = data.get('County', None)
        peal.country = data.get('Country', None)
    return peal
