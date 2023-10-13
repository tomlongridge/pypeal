from __future__ import annotations
from dataclasses import dataclass
import io
import logging
from enum import Enum
import os
from typing import ClassVar
import xml.etree.ElementTree as ET
import zipfile

import requests

from pypeal.db import Database
from pypeal.config import get_config

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

    @classmethod
    def from_method(cls, name: str, exact_match: bool = False) -> Stage:
        for stage in Stage:
            stage_name = str(stage).lower()
            if (exact_match and name == stage_name) or \
               (not exact_match and name.lower().endswith(stage_name)):
                return stage


@dataclass
class Method:

    __cache: ClassVar[dict[str, Method]] = {}

    full_name: str
    name: str = None
    is_differential: bool = False
    is_little: bool = False
    is_plain: bool = False
    is_treble_dodging: bool = False
    classification: str = None
    stage: Stage = None
    id: str = None

    def __str__(self) -> str:
        return self.full_name

    @classmethod
    def get(cls, id: str) -> Method:
        if id not in cls.__cache:
            result = Database.get_connection().query(
                'SELECT full_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id ' +
                'FROM methods WHERE id = %s', (id,)).fetchone()
            cls.__cache[id] = Method(*result[:-2], Stage(result[-2]), result[-1])
        return cls.__cache[id]

    @classmethod
    def get_by_name(cls, name: str):
        results = Database.get_connection().query(
            'SELECT full_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id FROM methods ' +
            f'WHERE full_name = "{name}"').fetchall()
        return cls.__with_cache([Method(*result[:-2], Stage(result[-2]), result[-1]) for result in results])

    @classmethod
    def search(cls,
               name: str = None,
               is_differential: bool = None,
               is_little: bool = None,
               is_plain: bool = None,
               is_treble_dodging: bool = None,
               classification: str = None,
               stage: Stage = None,
               exact_match: bool = False) -> list[Method]:
        query = 'SELECT full_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id ' + \
                'FROM methods WHERE 1=1 '
        params = {}
        if name:
            if exact_match:
                query += 'AND name = %(name)s '
                params['name'] = f'{name}'
            else:
                query += 'AND name LIKE %(name)s '
                params['name'] = f'%{name}%'
        if is_differential is not None:
            query += 'AND is_differential = %(is_differential)s '
            params['is_differential'] = is_differential
        if is_little is not None:
            query += 'AND is_little = %(is_little)s '
            params['is_little'] = is_little
        if is_plain is not None:
            query += 'AND is_plain = %(is_plain)s '
            params['is_plain'] = is_plain
        if is_treble_dodging is not None:
            query += 'AND is_treble_dodging = %(is_treble_dodging)s '
            params['is_treble_dodging'] = is_treble_dodging
        if classification:
            query += 'AND classification = %(classification)s '
            params['classification'] = classification
        if stage:
            query += 'AND stage = %(stage)s '
            params['stage'] = stage.value
        results = Database.get_connection().query(query, params).fetchall()
        return cls.__with_cache([Method(*result[:-2], Stage(result[-2]), result[-1]) for result in results])

    @classmethod
    def get_all(cls) -> list[Method]:
        results = Database.get_connection().query(
            'SELECT full_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id ' +
            'FROM methods').fetchall()
        return cls.__with_cache([Method(*result[:-2], Stage(result[-2]), result[-1]) for result in results])

    def commit(self):
        Database.get_connection().query(
            'INSERT INTO methods (full_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (self.full_name, self.name, self.is_differential, self.is_little, self.is_plain, self.is_treble_dodging, self.classification,
             self.stage.value, self.id))
        Database.get_connection().commit()

    @classmethod
    def update(cls):

        logger.debug('Disable foreign keys and truncate existing methods data')
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE methods;')

        method_file_url = get_config('methods', 'url')
        method_file_name = os.path.basename(method_file_url).replace('.zip', '')
        logger.info(f'Updating method library from {method_file_url}')

        if method_file_url.startswith('http'):
            response = requests.get(method_file_url)
            method_data = response.content
        else:
            with open(method_file_url, 'rb') as f:
                method_data = f.read()

        with zipfile.ZipFile(io.BytesIO(method_data)) as method_zip:
            with method_zip.open(method_file_name) as method_xml_file:
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
                    full_name=method.find(f'{XML_NAMESPACE}title').text,
                    is_differential=is_differential,
                    is_little=is_little,
                    is_plain=is_plain,
                    is_treble_dodging=is_treble_dodging
                )
                method_obj.commit()
                logger.debug(f'Added method {method_obj} to database')

        logger.debug('Reinstate foreign key checks')
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')

    @classmethod
    def __with_cache(cls, results: list[Method]) -> list[Method]:
        methods = []
        for method in results:
            if method.id not in cls.__cache:
                cls.__cache[method.id] = method
            methods.append(cls.__cache[method.id])
        return methods
