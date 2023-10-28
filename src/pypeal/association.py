from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

from pypeal.db import Database

FIELD_LIST: list[str] = ['name']


@dataclass
class Association:

    __cache: ClassVar[dict[int, Association]] = {}

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
        if id not in cls.__cache:
            result = Database.get_connection().query(
                f'SELECT {",".join(FIELD_LIST)}, id ' +
                'FROM associations WHERE id = %s', (id,)).fetchone()
            cls.__cache[id] = Association(*result)
        return cls.__cache[id]

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
        return cls.__with_cache([Association(*result) for result in results])

    @classmethod
    def __with_cache(cls, results: list[Association]) -> list[Association]:
        associations = []
        for association in results:
            if association.id not in cls.__cache:
                cls.__cache[association.id] = association
            associations.append(cls.__cache[association.id])
        return associations
