from __future__ import annotations
from dataclasses import dataclass
from pypeal.cache import Cache

from pypeal.db import Database

FIELD_LIST: list[str] = ['name', 'is_user_added', 'id']


@dataclass
class Association():

    name: str = None
    is_user_added: bool = True
    id: int = None

    def __str__(self):
        return self.name

    def __hash__(self) -> int:
        return hash(self.id)

    def commit(self):
        result = Database.get_connection().query(
            f'INSERT INTO associations ({",".join(FIELD_LIST)}) ' +
            f'VALUES ({("%s,"*len(FIELD_LIST)).strip(",")})',
            (self.name, self.is_user_added, self.id))
        Database.get_connection().commit()
        if self.is_user_added:
            self.id = result.lastrowid
        Cache.get_cache().add(self.__class__.__name__, self.id, self)

    @classmethod
    def get(cls, id: int) -> Association:
        if (association := Cache.get_cache().get(cls.__name__, id)) is not None:
            return association
        else:
            result = Database.get_connection().query(
                f'SELECT {",".join(FIELD_LIST)} ' +
                'FROM associations WHERE id = %s', (id,)).fetchone()
            return Cache.get_cache().add(cls.__name__, id, Association(*result)) if result else None

    @classmethod
    def search(cls,
               name: str,
               exact_match: bool = False) -> list[Association]:
        query = f'SELECT {",".join(FIELD_LIST)} ' + \
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
        return Cache.get_cache().add_all(cls.__name__, {result[-1]: Association(*result) for result in results})

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        # Only clear the user-added associations
        Database.get_connection().query('DELETE FROM associations WHERE is_user_added = 1')
        Database.get_connection().commit()
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
        Cache.get_cache().clear(cls.__name__)
