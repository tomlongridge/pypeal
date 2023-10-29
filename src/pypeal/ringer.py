from __future__ import annotations
from dataclasses import dataclass

from pypeal.db import Database
from pypeal.entity import CacheableEntity


@dataclass
class Ringer(CacheableEntity):

    last_name: str
    given_names: str
    id: int = None

    @property
    def name(self) -> str:
        return f'{self.given_names} {self.last_name}'

    def __str__(self) -> str:
        return self.name

    def commit(self):
        if self.id:
            raise SystemError('Cannot commit a ringer that already has an ID')
        result = Database.get_connection().query(
            'INSERT INTO ringers (last_name, given_names) VALUES (%s, %s)', (self.last_name, self.given_names))
        Database.get_connection().commit()
        self.id = result.lastrowid

    def add_alias(self, last_name: str, given_names: str):
        Database.get_connection().query(
            'INSERT INTO ringers (last_name, given_names, link_id) VALUES (%s, %s, %s)', (last_name, given_names, self.id))
        Database.get_connection().commit()

    @classmethod
    def get(cls, id: int) -> Ringer:
        if (ringer := cls._from_cache(id)) is not None:
            return ringer
        else:
            # Get ringers with no link ID (i.e. the actual ringer, not aliases)
            result = Database.get_connection().query(
                'SELECT last_name, given_names, id FROM ringers WHERE id = %s AND link_id IS NULL', (id,)).fetchone()
            return cls._cache_result(result)

    @classmethod
    def get_by_full_name(cls, name: str) -> list[Ringer]:
        results = Database.get_connection().query(
            'SELECT last_name, given_names, id FROM ringers ' +
            f'WHERE CONCAT_WS(" ", given_names, last_name) = "{name}"' +
            'AND link_id IS NULL ' +
            'OR (id IN (SELECT link_id FROM ringers ' +
            f'WHERE CONCAT_WS(" ", given_names, last_name) = "{name}"))').fetchall()
        return cls._cache_results(results)

    @classmethod
    def get_by_name(cls, last_name: str = None, given_names: str = None) -> list[Ringer]:
        results = Database.get_connection().query(
            'SELECT last_name, given_names, id FROM ringers ' +
            'WHERE ' +
            f'(last_name LIKE "{last_name if last_name and len(last_name.strip()) else "%"}" ' +
            f'AND given_names LIKE "{given_names if given_names and len(given_names.strip()) else "%"}") ' +
            'AND link_id IS NULL ' +
            'OR (id IN (SELECT link_id FROM ringers ' +
            'WHERE ' +
            f'(last_name LIKE "{last_name if last_name and len(last_name.strip()) else "%"}" ' +
            f'AND given_names LIKE "{given_names if given_names and len(given_names.strip()) else "%"}")))').fetchall()
        return cls._cache_results(results)

    @classmethod
    def get_all(cls) -> list[Ringer]:
        results = Database.get_connection().query('SELECT last_name, given_names, id FROM ringers').fetchall()
        return cls._cache_results(results)

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE ringers')
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
        Database.get_connection().commit()
        cls._clear_cache()
