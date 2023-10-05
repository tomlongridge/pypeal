from __future__ import annotations
from dataclasses import dataclass
import io
import logging
from enum import Enum
import xml.etree.ElementTree as ET
import zipfile

import requests

from pypeal.db import Database

METHOD_DEFINITION_URL = 'https://methods.cccbr.org.uk/xml/'
METHOD_DEFINITION_FILE_NAME = 'CCCBR_methods.xml'
XML_NAMESPACE = '{http://www.cccbr.org.uk/methods/schemas/2007/05/methods}'

logger = logging.getLogger('pypeal')


class Stage(Enum):
    TWO = 2
    SINGLES = 3
    MINIMUS = 4
    DOUBLES = 5
    MINOR = 6
    TRIPLES = 7
    MAJOR = 8
    CATERS = 9
    ROYAL = 10
    CINQUES = 11
    MAXIMUS = 12
    SEXTUPLES = 13
    FOURTEEN = 14
    SEPTUPLES = 15
    SIXTEEN = 16
    OCTUPLES = 17
    EIGHTEEN = 18
    NONUPLES = 19
    TWENTY = 20
    TWENTY_ONE = 21
    TWENTY_TWO = 22

    def __str__(self):
        return self.name.replace('_', ' ').capitalize()


@dataclass
class Method:

    # __cache: ClassVar[dict[int, Method]] = {}

    stage: Stage
    classification: str
    name: str
    is_differential: bool
    is_little: bool
    is_plain: bool
    is_treble_dodging: bool
    id: int = None

    def __str__(self) -> str:
        text = ''
        if self.name:
            text += self.name + ' '
        if self.is_differential:
            text += 'Differential '
        if self.is_little:
            text += 'Little '
        if self.classification and self.classification != 'Hybrid':
            text += self.classification + ' '
        text += str(self.stage)
        return text

    def commit(self):
        Database.get_connection().query(
            'INSERT INTO methods (id, stage, is_differential, is_little, is_plain, is_treble_dodging, classification, name) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
            (self.id, self.stage.value, self.is_differential, self.is_little, self.is_plain, self.is_treble_dodging, self.classification,
             self.name))
        Database.get_connection().commit()

    @classmethod
    def update(cls):

        logger.debug('Disable foreign keys and truncate existing methods data')
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE methods;')

        logger.info(f'Updating method library from {METHOD_DEFINITION_URL}')
        response = requests.get(f'{METHOD_DEFINITION_URL}/{METHOD_DEFINITION_FILE_NAME}.zip')
        with zipfile.ZipFile(io.BytesIO(response.content)) as method_zip:
            with method_zip.open(METHOD_DEFINITION_FILE_NAME) as method_xml_file:
                method_xml = method_xml_file.read()

        logger.debug('Parsing method XML')
        tree = ET.fromstring(method_xml)

        logger.debug('Inserting methods into database')
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
                    stage=Stage(int(stage)),
                    classification=classification,
                    name=method.find(f'{XML_NAMESPACE}name').text,
                    is_differential=is_differential,
                    is_little=is_little,
                    is_plain=is_plain,
                    is_treble_dodging=is_treble_dodging
                ).commit()
                logger.debug(f'Added method {method_obj} to database')

        logger.debug('Reinstate foreign key checks')
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
