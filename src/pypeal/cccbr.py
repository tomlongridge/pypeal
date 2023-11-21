import io
import logging
import os
import zipfile

import xml.etree.ElementTree as ET

import requests
from pypeal import utils
from pypeal.config import get_config
from pypeal.db import Database
from pypeal.method import Method

XML_NAMESPACE = '{http://www.cccbr.org.uk/methods/schemas/2007/05/methods}'

_logger = logging.getLogger('pypeal')


def update_methods():

    _logger.debug('Disable foreign keys and truncate existing methods data')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
    Database.get_connection().query('TRUNCATE TABLE methods;')

    _logger.info('Downloading method data from CCCBR...')
    method_file_url = get_config('cccbr', 'methods_url')
    method_file_name = os.path.basename(method_file_url).replace('.zip', '')

    if method_file_url.startswith('http'):
        response = requests.get(method_file_url)
        method_data = response.content
    else:
        with open(method_file_url, 'rb') as f:
            method_data = f.read()

    if method_file_url.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(method_data)) as method_zip:
            with method_zip.open(method_file_name) as method_xml_file:
                method_xml = method_xml_file.read()
    else:
        method_xml = method_data

    _logger.info('Adding method data to database...')
    _logger.debug('Parsing method XML')
    tree = ET.fromstring(method_xml)

    _logger.debug('Inserting methods into database')
    for method_set in tree.findall(f'./{XML_NAMESPACE}methodSet'):
        stage = method_set.find(f'{XML_NAMESPACE}properties/{XML_NAMESPACE}stage').text
        classification_element = method_set.find(f'{XML_NAMESPACE}properties/{XML_NAMESPACE}classification')
        classification = classification_element.text
        is_differential = 'differential' in classification_element.attrib
        is_little = 'little' in classification_element.attrib
        is_plain = 'plain' in classification_element.attrib
        is_treble_dodging = 'trebleDodging' in classification_element.attrib
        for method in method_set.findall(f'{XML_NAMESPACE}method'):
            method_obj = Method(
                id=method.attrib['id'],
                stage=int(stage),
                classification=classification,
                name=utils.get_searchable_string(method.find(f'{XML_NAMESPACE}name').text),
                full_name=method.find(f'{XML_NAMESPACE}title').text,
                is_differential=is_differential,
                is_little=is_little,
                is_plain=is_plain,
                is_treble_dodging=is_treble_dodging
            )
            method_obj.commit()
            _logger.debug(f'Added method {method_obj} to database')

    _logger.debug('Reinstate foreign key checks')
    Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
