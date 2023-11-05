import csv
import logging

import requests
from pypeal import utils
from pypeal.association import Association
from pypeal.config import get_config
from pypeal.db import Database
from pypeal.tower import Bell, Tower


_logger = logging.getLogger('pypeal')


class DoveError(Exception):
    pass


def update_towers():

    _logger.debug('Disable foreign keys and truncate existing tower data')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
    Database.get_connection().query('TRUNCATE TABLE towers;')

    file_url = get_config('dove', 'towers_url')
    if file_url.startswith('http'):
        response = requests.get(file_url)
        response.encoding = 'utf-8-sig'
        data = response.text
    else:
        with open(file_url, 'r', encoding='utf-8-sig') as f:
            data = f.read()

    tower_ids = []
    for line in csv.DictReader(data.splitlines(), delimiter=',', quotechar='"'):
        if line['TowerID'].startswith('#'):
            continue  # comment line
        if line['TowerID'] in tower_ids:
            continue  # todo: handle multiple rings in one line
        tower_obj = Tower(towerbase_id=line['TowerBase'],
                          place=line['Place'],
                          sub_place=line['Place2'],
                          dedication=line['Dedicn'],
                          county=line['County'],
                          country=line['Country'],
                          country_code=line['ISO3166code'],
                          latitude=float(line['Lat']) if len(line['Lat']) > 0 else None,
                          longitude=line['Long'] if len(line['Long']) > 0 else None,
                          bells=line['Bells'],
                          tenor_weight=int(line['Wt']),
                          tenor_note=utils.convert_musical_key(line['Note']),
                          id=line['TowerID'])
        tower_obj.commit()
        tower_ids.append(line['TowerID'])
        _logger.debug(f'Added tower {tower_obj} to database')

    _logger.debug('Reinstate foreign key checks')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')


def update_associations():

    _logger.debug('Disable foreign keys and truncate existing association data')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
    Database.get_connection().query('TRUNCATE TABLE associations;')

    file_url = get_config('dove', 'regions_url')
    if file_url.startswith('http'):
        response = requests.get(file_url)
        response.encoding = 'utf-8-sig'
        data = response.text
    else:
        with open(file_url, 'r', encoding='utf-8-sig') as f:
            data = f.read()

    for line in csv.DictReader(data.splitlines(), delimiter=',', quotechar='"'):
        match line['Category']:
            case 'Association':
                association_obj = Association(name=line['Name'],
                                              id=line['ID'])
                association_obj.commit()
                _logger.debug(f'Added association "{association_obj}" to database')

    _logger.debug('Reinstate foreign key checks')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')


def update_bells():

    _logger.debug('Disable foreign keys and truncate existing bell data')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
    Database.get_connection().query('TRUNCATE TABLE bells;')

    file_url = get_config('dove', 'bells_url')
    if file_url.startswith('http'):
        response = requests.get(file_url)
        response.encoding = 'utf-8-sig'
        data = response.text
    else:
        with open(file_url, 'r', encoding='utf-8-sig') as f:
            data = f.read()

    for line in csv.DictReader(data.splitlines(), delimiter=',', quotechar='"'):
        if line['Bell ID'].startswith('#'):
            continue  # comment line
        elif not line['Bell Role'].isnumeric():
            continue  # omit any bells not in a ring (e.g sanctus)
        cast_year = line['Cast Date']
        if cast_year.startswith('c'):
            cast_year = cast_year[1:]
        bell_obj: Bell = Bell(tower_id=int(line['Tower ID']),
                              role=int(line['Bell Role']),
                              weight=int(line['Weight (lbs)']),
                              note=utils.convert_musical_key(line['Note']),
                              cast_year=int(cast_year),
                              founder=line['Founder'],
                              id=int(line['Bell ID']))
        bell_obj.commit()
        _logger.debug(f'Added bell {bell_obj.id} to database')

    _logger.debug('Reinstate foreign key checks')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
