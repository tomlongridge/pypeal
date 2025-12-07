from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from pypeal import utils
from pypeal.cache import Cache

from pypeal.db import Database

METHOD_NAME_EXCEPTIONS_LITTLE_PREFIXED_IN_NAME = ['Little Grandsire']
METHOD_NAME_EXCEPTIONS_BOB_CLASSIFICATION_NOT_USED = ['Grandsire', 'Union', 'Little Grandsire', 'Double Grandsire']


class Stage(IntEnum):

    UNUS = 1
    MICROMUS = 2
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
        return None


class Classification(Enum):

    ALLIANCE = 'Alliance'
    BOB = 'Bob'
    DELIGHT = 'Delight'
    HYBRID = 'Hybrid'
    PLACE = 'Place'
    SURPRISE = 'Surprise'
    TREBLE_BOB = 'Treble Bob'
    TREBLE_PLACE = 'Treble Place'

    def __str__(self):
        return self.value


@dataclass
class Method():

    full_name: str = None
    searchable_name: str = None
    name: str = None
    is_differential: bool = None
    is_little: bool = None
    is_plain: bool = None
    is_treble_dodging: bool = None
    classification: Classification = None
    stage: Stage = None
    id: str = None

    def __init__(self,
                 full_name: str = None,
                 searchable_name: str = None,
                 name: str = None,
                 is_differential: bool = None,
                 is_little: bool = None,
                 is_plain: bool = None,
                 is_treble_dodging: bool = None,
                 classification: str = None,
                 stage: int = None,
                 id: str = None):
        self.full_name = full_name
        self.searchable_name = searchable_name
        self.name = name
        self.is_differential = is_differential
        self.is_little = is_little
        self.is_plain = is_plain
        self.is_treble_dodging = is_treble_dodging
        self.classification = Classification(classification) if classification else None
        self.stage = Stage(stage) if stage else None
        self.id = id

    def get_calculated_name(self, show_classification: bool = True, show_stage: bool = True) -> str:
        value = ''
        value += f'{self.name}' if self.name else ''
        value += ' Differential' if self.is_differential else ''
        value += ' Little' if self.is_little and self.name not in METHOD_NAME_EXCEPTIONS_LITTLE_PREFIXED_IN_NAME else ''
        if show_classification and \
                self.classification not in [None, Classification.HYBRID] and \
                self.name not in METHOD_NAME_EXCEPTIONS_BOB_CLASSIFICATION_NOT_USED:
            value += f' {self.classification}'
        # if f'{value.strip()} {self.stage}' != self.full_name:
        #     raise ValueError(f'Calculated name ({value.strip()} {self.stage}) does not match full name ({self.full_name})')
        value += f' {self.stage}' if show_stage and self.stage else ''
        return value.strip()

    def __str__(self) -> str:
        if self.full_name:
            return self.full_name
        else:
            return self.get_calculated_name()

    def __hash__(self) -> int:
        return hash(self.id)

    def commit(self):
        Database.get_connection().query(
            'INSERT INTO methods (full_name, searchable_name, name, is_differential, is_little, is_plain, is_treble_dodging, ' +
            'classification, stage, id) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (self.full_name, self.searchable_name, self.name, self.is_differential, self.is_little, self.is_plain, self.is_treble_dodging,
             self.classification.value if self.classification else None, self.stage.value if self.stage else None, self.id))
        Database.get_connection().commit()
        Cache.get_cache().add(self.__class__.__name__, self.id, self)

    @classmethod
    def get(cls, id: str) -> Method:
        if (method := Cache.get_cache().get(cls.__name__, id)) is not None:
            return method
        else:
            result = Database.get_connection().query(
                'SELECT full_name, searchable_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, ' +
                'stage, id ' +
                'FROM methods WHERE id = %s', (id,)).fetchone()
            return Cache.get_cache().add(cls.__name__, result[-1], Method(*result)) if result else None

    @classmethod
    def get_by_name(cls, name: str) -> Method:
        result = Database.get_connection().query(
            'SELECT full_name, searchable_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id ' +
            'FROM methods ' +
            f'WHERE full_name = "{name}"').fetchone()
        return Cache.get_cache().add(cls.__name__, result[-1], Method(*result)) if result else None

    @classmethod
    def search(cls,
               name: str = None,
               is_differential: bool = None,
               is_little: bool = None,
               is_plain: bool = None,
               is_treble_dodging: bool = None,
               classification: Classification = None,
               stage: Stage = None,
               exact_match: bool = False,
               limit: int = 30) -> list[Method]:

        if exact_match:
            if name and '%' in name:
                raise ValueError('Exact match specified in method search, but name contains wildcard')
        else:
            name = f'{name}%' if name and '%' not in name else name

        query = 'SELECT full_name, searchable_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, ' + \
                'stage, id ' + \
                'FROM methods ' + \
                'WHERE 1=1 '
        params = {}
        if name:
            name = utils.get_searchable_string(name)
            if exact_match:
                query += 'AND searchable_name = %(name)s '
                params['name'] = f'{name}'
            else:
                query += 'AND searchable_name LIKE %(name)s '
                params['name'] = f'%{name}%'
        elif exact_match:
            query += 'AND name IS NULL '
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
            params['classification'] = classification.value
        if stage:
            query += 'AND stage = %(stage)s '
            params['stage'] = stage.value
        query += 'ORDER BY (SELECT COUNT(*) FROM pealmethods WHERE pealmethods.method_id = methods.id) DESC, methods.full_name ASC '
        query += 'LIMIT %(limit)s'
        params['limit'] = limit

        results = Database.get_connection().query(query, params).fetchall()
        return Cache.get_cache().add_all(cls.__name__, {result[-1]: Method(*result) for result in results})

    @classmethod
    def get_all(cls) -> list[Method]:
        results = Database.get_connection().query(
            'SELECT full_name, searchable_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id ' +
            'FROM methods').fetchall()
        return Cache.get_cache().add_all(cls.__name__, {result[-1]: Method(*result) for result in results})

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE methods')
        Database.get_connection().commit()
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
        Cache.get_cache().clear(cls.__name__)
