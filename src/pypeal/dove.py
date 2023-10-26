import csv
import logging

import requests
from pypeal.config import get_config
from pypeal.db import Database
from pypeal.tower import Tower


_logger = logging.getLogger('pypeal')


def update_towers():

    _logger.debug('Disable foreign keys and truncate existing tower data')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
    Database.get_connection().query('TRUNCATE TABLE towers;')

    tower_file_url = get_config('towers', 'url')
    if tower_file_url.startswith('http'):
        response = requests.get(tower_file_url)
        response.encoding = 'utf-8-sig'
        tower_data = response.text
    else:
        with open(tower_file_url, 'r', encoding='utf-8-sig') as f:
            tower_data = f.read()

    tower_ids = []
    for tower in csv.DictReader(tower_data.splitlines(), delimiter=',', quotechar='"'):
        if tower['TowerID'].startswith('#'):
            continue  # comment line
        if tower['TowerID'] in tower_ids:
            continue  # todo: handle multiple rings in one tower
        tower_obj = Tower(place=tower['Place'],
                          place_2=tower['Place2'],
                          dedication=tower['Dedicn'],
                          county=tower['County'],
                          country=tower['Country'],
                          country_code=tower['ISO3166code'],
                          latitude=float(tower['Lat']) if len(tower['Lat']) > 0 else None,
                          longitude=tower['Long'] if len(tower['Long']) > 0 else None,
                          bells=tower['Bells'],
                          tenor_weight=int(tower['Wt']),
                          tenor_note=tower['Note'],
                          id=tower['TowerID'])
        tower_obj.commit()
        tower_ids.append(tower['TowerID'])
        _logger.debug(f'Added tower {tower_obj} to database')

    _logger.debug('Reinstate foreign key checks')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
