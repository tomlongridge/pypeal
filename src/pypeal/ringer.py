from __future__ import annotations
from dataclasses import dataclass
from pypeal.cache import Cache

from pypeal.db import Database

FIELD_LIST: list[str] = ['last_name', 'given_names', 'is_composer', 'link_id']


@dataclass
class Ringer():

    last_name: str
    given_names: str
    is_composer: bool = False
    link: Ringer = None
    id: int = None

    def __init__(self,
                 last_name: str,
                 given_names: str,
                 is_composer: int = 0,
                 link_id: int = None,
                 id: int = None):
        self.last_name = last_name
        self.given_names = given_names
        self.is_composer = is_composer == 1
        self.link = Ringer.get(link_id) if link_id else None
        self.id = id

    @property
    def name(self) -> str:
        text = ''
        text += f'{self.given_names} ' if self.given_names else ''
        text += f'{self.last_name}' if self.last_name else ''
        return text if len(text) > 0 else None

    def __str__(self) -> str:
        return self.name

    def commit(self):
        if self.id:
            result = Database.get_connection().query(
                'UPDATE ringers ' +
                'SET last_name = %s, given_names = %s, is_composer = %s, link_id = %s ' +
                'WHERE id = %s',
                (self.last_name, self.given_names, self.is_composer, self.link.id if self.link else None, self.id))
            Database.get_connection().commit()
        else:
            result = Database.get_connection().query(
                f'INSERT INTO ringers ({",".join(FIELD_LIST)}) VALUES (%s, %s, %s, %s)',
                (self.last_name, self.given_names, self.is_composer, self.link.id if self.link else None))
            Database.get_connection().commit()
            self.id = result.lastrowid
        Cache.get_cache().add(self.__class__.__name__, self.id, self)

    def add_alias(self, last_name: str, given_names: str, is_primary: bool = False):
        if is_primary:
            # Create new alias with current details then update self to the new details
            # (this saves updating all references to self.id)
            new_alias = Ringer(self.last_name, self.given_names, self.is_composer, self.id)
            new_alias.commit()
            self.last_name = last_name
            self.given_names = given_names
            self.is_composer = self.is_composer
            self.link = None
            self.commit()
        else:
            alias = Ringer(last_name, given_names, False, self.id)
            alias.commit()
            return alias

    def get_aliases(self, last_name: str = None, given_names: str = None) -> list[Ringer]:
        query = f'SELECT {",".join(FIELD_LIST)}, id ' + \
                 'FROM ringers ' + \
                 'WHERE link_id = %(id)s '
        params = {'id': self.id}
        if last_name:
            query += 'AND last_name = %(last_name)s '
            params['last_name'] = last_name
        if given_names:
            query += 'AND given_names = %(given_names)s '
            params['given_names'] = given_names
        results = Database.get_connection().query(query, params=params).fetchall()
        return Cache.get_cache().add_all(self.__class__.__name__, {result[-1]: Ringer(*result) for result in results})

    def get_peals(self):
        from pypeal.peal import Peal
        results = Database.get_connection().query(
            'SELECT peal_id FROM pealringers WHERE ringer_id = %s ',
            (self.id,)).fetchall()
        return [Peal.get(result[0]) for result in results]

    @classmethod
    def get(cls, id: int) -> Ringer:
        if (ringer := Cache.get_cache().get(cls.__name__, id)) is not None:
            return ringer
        else:
            # Get ringers with no link ID (i.e. the actual ringer, not aliases)
            result = Database.get_connection().query(
                f'SELECT {",".join(FIELD_LIST)}, id FROM ringers WHERE id = %s AND link_id IS NULL', (id,)).fetchone()
            return Cache.get_cache().add(cls.__name__, result[-1], Ringer(*result)) if result else None

    @classmethod
    def get_by_name(cls,
                    last_name: str = None,
                    given_names: str = None,
                    is_composer: bool = None,
                    exact_match: bool = False) -> list[Ringer]:

        if last_name is None and given_names is None:
            raise ValueError('Either last_name or given_names must be specified in ringer search')

        if exact_match:
            if last_name and '%' in last_name:
                raise ValueError('Exact match specified in ringer search, but last_name contains wildcard')
            if given_names and '%' in given_names:
                raise ValueError('Exact match specified in ringer search, but given_names contains wildcard')
        else:
            last_name = f'{last_name}%' if last_name and '%' not in last_name else last_name
            given_names = f'{given_names}%' if given_names and '%' not in given_names else given_names

        name_clause = ''
        params = {}
        if last_name:
            name_clause += f'AND @tbl.last_name {"=" if exact_match else "LIKE"} %(last_name)s '
            params['last_name'] = last_name.strip()
        elif exact_match:
            name_clause += 'AND @tbl.last_name IS NULL '
        if given_names:
            name_clause += f'AND @tbl.given_names {"=" if exact_match else "LIKE"} %(given_names)s '
            params['given_names'] = given_names.strip()
        elif exact_match:
            name_clause += 'AND @tbl.given_names IS NULL '
        if is_composer is not None:
            name_clause += 'AND @tbl.is_composer = %(is_composer)s '
            params['is_composer'] = is_composer

        results = Database.get_connection().query(
            f'SELECT {",".join(FIELD_LIST)}, id FROM ringers AS r ' +
            f'WHERE 1=1 {name_clause.replace("@tbl", "r")} AND r.link_id IS NULL ' +
            'OR (r.id IN (SELECT lr.link_id FROM ringers AS lr ' +
            f'WHERE 1=1 {name_clause.replace("@tbl", "lr")} AND lr.link_id IS NOT NULL))',
            params
        ).fetchall()
        return Cache.get_cache().add_all(cls.__name__, {result[-1]: Ringer(*result) for result in results})

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE ringers')
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
        Database.get_connection().commit()
        Cache.get_cache().clear(cls.__name__)
