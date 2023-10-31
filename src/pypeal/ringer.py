from __future__ import annotations
from dataclasses import dataclass

from pypeal.db import Database
from pypeal.entity import CacheableEntity

FIELD_LIST: list[str] = ['last_name', 'given_names', 'is_composer']


@dataclass
class Ringer(CacheableEntity):

    last_name: str
    given_names: str
    is_composer: bool = False
    id: int = None

    def __init__(self, last_name: str, given_names: str, is_composer: int = 0, id: int = None):
        self.last_name = last_name
        self.given_names = given_names
        self.is_composer = is_composer == 1
        self.id = id

    @property
    def name(self) -> str:
        return f'{self.given_names} {self.last_name}'

    def __str__(self) -> str:
        return self.name

    def commit(self):
        if self.id:
            result = Database.get_connection().query(
                'UPDATE ringers ' +
                'SET last_name = %s, given_names = %s, is_composer = %s ' +
                'WHERE id = %s',
                (self.last_name, self.given_names, self.is_composer, self.id))
            Database.get_connection().commit()
        else:
            result = Database.get_connection().query(
                f'INSERT INTO ringers ({",".join(FIELD_LIST)}) VALUES (%s, %s, %s)',
                (self.last_name, self.given_names, self.is_composer))
            Database.get_connection().commit()
            self.id = result.lastrowid

    def add_alias(self, last_name: str, given_names: str):
        Database.get_connection().query(
            f'INSERT INTO ringers ({",".join(FIELD_LIST)}, link_id) VALUES (%s, %s, %s, %s)',
            (last_name, given_names, None, self.id))
        Database.get_connection().commit()

    @classmethod
    def get(cls, id: int) -> Ringer:
        if (ringer := cls._from_cache(id)) is not None:
            return ringer
        else:
            # Get ringers with no link ID (i.e. the actual ringer, not aliases)
            result = Database.get_connection().query(
                f'SELECT {",".join(FIELD_LIST)}, id FROM ringers WHERE id = %s AND link_id IS NULL', (id,)).fetchone()
            return cls._cache_result(result)

    @classmethod
    def get_by_full_name(cls, name: str, is_composer: bool = None) -> list[Ringer]:
        results = Database.get_connection().query(
            f'SELECT {",".join(FIELD_LIST)}, id FROM ringers ' +
            'WHERE CONCAT_WS(" ", given_names, last_name) = %(name)s ' +
            'AND link_id IS NULL ' +
            ('AND is_composer = %(is_composer)s ' if is_composer is not None else ' ') +
            'OR (id IN (SELECT link_id FROM ringers WHERE CONCAT_WS(" ", given_names, last_name) = %(name)s))',
            {
                'name': name.strip(),
                'composer': is_composer
            }
        ).fetchall()
        return cls._cache_results(results)

    @classmethod
    def get_by_name(cls, last_name: str = None, given_names: str = None, is_composer: bool = None) -> list[Ringer]:
        results = Database.get_connection().query(
            f'SELECT {",".join(FIELD_LIST)}, id FROM ringers ' +
            'WHERE (last_name LIKE %(last_name)s AND given_names LIKE %(given_names)s) ' +
            'AND link_id IS NULL ' +
            ('AND is_composer = %(is_composer)s ' if is_composer is not None else ' ') +
            'OR (id IN (SELECT link_id FROM ringers WHERE last_name LIKE %(last_name)s AND given_names LIKE %(given_names)s))',
            {
                'last_name': last_name.strip() if last_name else '%',
                'given_names': given_names.strip() if given_names else '%',
                'composer': is_composer
            }
        ).fetchall()
        return cls._cache_results(results)

    @classmethod
    def get_all(cls) -> list[Ringer]:
        results = Database.get_connection().query(f'SELECT {",".join(FIELD_LIST)}, id FROM ringers').fetchall()
        return cls._cache_results(results)

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE ringers')
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
        Database.get_connection().commit()
        cls._clear_cache()
