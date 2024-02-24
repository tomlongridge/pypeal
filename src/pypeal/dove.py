import csv
import logging
import os
import pathlib
import re

import requests
from pypeal import utils
from pypeal.entities.association import Association
from pypeal.config import get_config
from pypeal.db import Database
from pypeal.entities.tower import Bell, Tower

CAST_YEAR_REGEX = \
    re.compile(r'c?\-?\d*?\s?\(?(?P<year>\d{4})\)?')

_logger = logging.getLogger('pypeal')


class DoveError(Exception):
    pass


def update_towers():

    _logger.debug('Disable foreign keys and truncate existing tower data')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
    Database.get_connection().query('TRUNCATE TABLE towers;')

    _logger.info('Downloading tower data from Dove...')
    file_url = get_config('dove', 'towers_url')
    if file_url.startswith('http'):
        response = requests.get(file_url)
        response.encoding = 'utf-8-sig'
        data = response.text
    else:
        with open(file_url, 'r', encoding='utf-8-sig') as f:
            data = f.read()

    _logger.info('Adding tower data to database...')
    tower_ids = []
    for line in csv.DictReader(data.splitlines(), delimiter=',', quotechar='"'):
        if line['TowerID'].startswith('#'):
            continue  # comment line
        if line['TowerID'] in tower_ids:
            continue  # todo: handle multiple rings in one line
        if len(line['County']) == len(line['Country']) == len(line['ISO3166code']) == 0:
            continue
        tower_obj = Tower(towerbase_id=int(line['TowerBase']) if len(line['TowerBase']) > 0 else None,
                          place=line['Place'] if len(line['Place']) > 0 else None,
                          sub_place=line['Place2'] if len(line['Place2']) > 0 else None,
                          dedication=line['Dedicn'] if len(line['Dedicn']) > 0 else None,
                          county=line['County'],
                          country=line['Country'],
                          country_code=line['ISO3166code'],
                          latitude=float(line['Lat']) if len(line['Lat']) > 0 else None,
                          longitude=line['Long'] if len(line['Long']) > 0 else None,
                          bells=int(line['Bells']),
                          tenor_weight=int(line['Wt']) if len(line['Wt']) > 0 else None,
                          tenor_note=utils.convert_musical_key(line['Note']),
                          id=int(line['TowerID']))
        tower_obj.commit()
        tower_ids.append(line['TowerID'])
        _logger.debug(f'Added tower {tower_obj} to database')

    _logger.debug('Reinstate foreign key checks')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')

    Database.get_connection().commit()


def update_associations():

    _logger.debug('Disable foreign keys and truncate existing association data')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
    Database.get_connection().query('DELETE FROM associations WHERE is_user_added = 0;')

    _logger.info('Downloading region data from Dove...')
    file_url = get_config('dove', 'regions_url')
    if file_url.startswith('http'):
        response = requests.get(file_url)
        response.encoding = 'utf-8-sig'
        data = response.text
    else:
        with open(file_url, 'r', encoding='utf-8-sig') as f:
            data = f.read()

    _logger.info('Adding region data to database...')
    for line in csv.DictReader(data.splitlines(), delimiter=',', quotechar='"'):
        match line['Category']:
            case 'Association':
                association_obj = Association(name=line['Name'],
                                              is_user_added=False,
                                              id=-1 * int(line['ID']))
                association_obj.commit()
                _logger.debug(f'Added association "{association_obj}" to database')

    _logger.debug('Reinstate foreign key checks')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')


def update_bells():

    _logger.debug('Disable foreign keys and truncate existing bell data')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
    Database.get_connection().query('TRUNCATE TABLE bells;')

    _logger.info('Downloading bell data from Dove...')
    file_url = get_config('dove', 'bells_url')
    if file_url.startswith('http'):
        response = requests.get(file_url)
        response.encoding = 'utf-8-sig'
        data = response.text
    else:
        with open(file_url, 'r', encoding='utf-8-sig') as f:
            data = f.read()

    _logger.info('Adding bell data to database...')
    for line in csv.DictReader(data.splitlines(), delimiter=',', quotechar='"'):

        if line['Bell ID'].startswith('#'):
            continue  # comment line
        elif not line['Bell Role'].isnumeric():
            continue  # omit any bells not in a ring (e.g sanctus)

        if line['Cast Date'] in ('', 'None', 'n/d'):
            cast_year = None
        elif match := re.match(CAST_YEAR_REGEX, line['Cast Date']):
            cast_year = int(match.group('year'))
        else:
            _logger.warn(f'Unexpected cast year \"{line["Cast Date"]}\" for bell {line["Bell ID"]}')
            continue

        weight = line['Weight (lbs)']
        if len(weight) == 0:
            weight = None
        elif weight.isnumeric():
            weight = int(weight)
        elif '.' in weight:
            weight = round(float(weight))
        else:
            _logger.warn(f'Unexpected weight "{weight}" for bell {line["Bell ID"]}')
            continue

        bell_obj: Bell = Bell(tower_id=int(line['Tower ID']),
                              role=int(line['Bell Role']),
                              weight=weight,
                              note=utils.convert_musical_key(line['Note']),
                              cast_year=cast_year,
                              founder=line['Founder'] if len(line['Founder']) > 0 else None,
                              id=int(line['Bell ID']))

        if bell_obj.tower is None:
            _logger.debug(f'Skipping bell {bell_obj.id} - no matching tower ({line["Tower ID"]})')
        else:
            bell_obj.commit()
            _logger.debug(f'Added bell {bell_obj.id} to database')

    _logger.debug('Reinstate foreign key checks')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')


def update_rings():

    _logger.debug('Disable foreign keys and truncate existing bell data')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
    Database.get_connection().query('TRUNCATE TABLE ringbells;')
    Database.get_connection().query('TRUNCATE TABLE rings;')

    for path in sorted(pathlib.Path(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'rings')).glob('*.sql')):
        Database.get_connection().run_script(path)

    _logger.debug('Reinstate foreign key checks')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
