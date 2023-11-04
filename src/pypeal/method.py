from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pypeal.cache import Cache

from pypeal.db import Database


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
class Method():

    full_name: str = None
    name: str = None
    is_differential: bool = None
    is_little: bool = None
    is_plain: bool = None
    is_treble_dodging: bool = None
    classification: str = None
    stage: Stage = None
    id: str = None

    @property
    def title(self) -> str:
        text = f'{self.name} ' if self.name else ''
        text += f'{self.classification} ' if self.classification else ''
        text += self.stage.name.capitalize() if self.stage else ''
        return text

    def __str__(self) -> str:
        return self.full_name

    @classmethod
    def get(cls, id: str) -> Method:
        if (method := Cache.get_cache().get(cls.__name__, id)) is not None:
            return method
        else:
            result = Database.get_connection().query(
                'SELECT full_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id ' +
                'FROM methods WHERE id = %s', (id,)).fetchone()
            return Cache.get_cache().add(cls.__name__, result[-1], Method(*result[:-2], Stage(result[-2]), result[-1]))

    @classmethod
    def get_by_name(cls, name: str):
        results = Database.get_connection().query(
            'SELECT full_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id FROM methods ' +
            f'WHERE full_name = "{name}"').fetchall()
        return Cache.get_cache().add_all(cls.__name__,
                                         {result[-1]: Method(*result[:-2], Stage(result[-2]), result[-1]) for result in results})

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
        return Cache.get_cache().add_all(cls.__name__,
                                         {result[-1]: Method(*result[:-2], Stage(result[-2]), result[-1]) for result in results})

    @classmethod
    def get_all(cls) -> list[Method]:
        results = Database.get_connection().query(
            'SELECT full_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id ' +
            'FROM methods').fetchall()
        return Cache.get_cache().add_all(cls.__name__,
                                         {result[-1]: Method(*result[:-2], Stage(result[-2]), result[-1]) for result in results})

    def commit(self):
        Database.get_connection().query(
            'INSERT INTO methods (full_name, name, is_differential, is_little, is_plain, is_treble_dodging, classification, stage, id) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (self.full_name, self.name, self.is_differential, self.is_little, self.is_plain, self.is_treble_dodging, self.classification,
             self.stage.value, self.id))
        Database.get_connection().commit()
        Cache.get_cache().add(self.__class__.__name__, self.id, self)
