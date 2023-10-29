from __future__ import annotations
from dataclasses import dataclass

from pypeal.db import Database
from pypeal.entity import CacheableEntity

FIELD_LIST: list[str] = ['name']


@dataclass
class Association(CacheableEntity):

    name: str = None
    id: int = None

    def __str__(self):
        return self.name

    def commit(self):
        Database.get_connection().query(
            f'INSERT INTO associations ({",".join(FIELD_LIST)}, id) ' +
            f'VALUES ({"%s" * len(FIELD_LIST)}, %s)',
            (self.name, self.id))
        Database.get_connection().commit()

    @classmethod
    def get(cls, id: int) -> Association:
        if (association := cls._from_cache(id)) is not None:
            return association
        else:
            result = Database.get_connection().query(
                f'SELECT {",".join(FIELD_LIST)}, id ' +
                'FROM associations WHERE id = %s', (id,)).fetchone()
            return cls._cache_result(result)

    @classmethod
    def search(cls,
               name: str,
               exact_match: bool = False) -> list[Association]:
        query = f'SELECT {",".join(FIELD_LIST)}, id ' + \
                'FROM associations WHERE 1=1 '
        params = {}
        name = name.replace('&', 'and')
        if exact_match:
            query += 'AND name = %(name)s '
            params['name'] = f'{name}'
        else:
            query += 'AND name LIKE %(name)s '
            params['name'] = f'%{name}%'
        results = Database.get_connection().query(query, params).fetchall()
        return cls._cache_results(results)
