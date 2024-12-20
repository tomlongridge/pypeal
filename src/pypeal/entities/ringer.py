from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pypeal.cache import Cache

from pypeal.db import Database
from pypeal.entities.tower import Tower

FIELD_LIST: list[str] = ['last_name', 'given_names', 'title', 'is_composer', 'link_id', 'date_to', 'home_tower_id']


class Ringer():

    def __init__(self, last_name: str = None, given_names: str = None, title: str = None):
        self.__names: list[Ringer._RingerName] = []
        self.__aliases: list[Ringer._RingerName] = []
        if last_name:
            self.__names.append(self._RingerName(last_name, given_names, title))

    def __str__(self) -> str:
        return self.__names[-1].name if self.__names else 'Unknown'

    def __hash__(self) -> int:
        return self.id

    @property
    def id(self) -> int:
        return self.__names[-1].id if self.__names else None

    @property
    def last_name(self) -> str:
        return self.__names[-1].last_name if self.__names else None

    @property
    def given_names(self) -> str:
        return self.__names[-1].given_names if self.__names else None

    @property
    def title(self) -> str:
        return self.__names[-1].title if self.__names else None

    @property
    def name(self) -> str:
        return self.get_name()

    @property
    def is_composer(self) -> bool:
        return self.__names[-1].is_composer if self.__names else False

    @is_composer.setter
    def is_composer(self, value: bool):
        self.__names[-1].is_composer = value

    @property
    def home_tower(self) -> Tower:
        return self.__names[-1].home_tower if self.__names else None

    @property
    def aliases(self) -> list[str]:
        return [alias.name for alias in self.__aliases]

    def get_name(self, date: datetime.date = None) -> str:
        if not self.__names:
            return 'Unknown'
        if date is None:
            return self.__names[-1].name
        else:
            ringer_name: Ringer._RingerName
            for ringer_name in self.__names:
                if ringer_name.date_to is None or ringer_name.date_to >= date:
                    return ringer_name.name
            raise ValueError(f'No name found for ringer {self.id} on date {date}')

    def commit(self):
        self.__names[-1].commit()
        for ringer_name in self.__names[:-1] + self.__aliases:
            ringer_name.link = self.__names[-1].id
            ringer_name.commit()

    def add_alias(self, last_name: str, given_names: str, is_primary: bool = False):
        if is_primary:
            # Create new alias with current details then update self to the new details
            # (this saves updating all references to self.id)
            original_name = self.__names[-1]
            self.__aliases.append(self._RingerName(original_name.last_name,
                                                   original_name.given_names,
                                                   link_id=original_name.id))
            original_name.last_name = last_name
            original_name.given_names = given_names
        else:
            self.__aliases.append(self._RingerName(last_name, given_names, link_id=self.id))

    def has_alias(self, last_name: str, given_names: str) -> bool:
        return any(alias.matches(last_name, given_names) for alias in self.__aliases) \
               or any(name.matches(last_name, given_names) for name in self.__names)

    def get_peals(self):
        from pypeal.entities.peal import Peal
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
            results = Database.get_connection().query(
                f'SELECT {",".join(FIELD_LIST)}, id FROM ringers ' +
                'WHERE id = %s OR link_id = %s ' +
                'ORDER BY date_to IS NULL, date_to ASC', (id, id)).fetchall()

            if not results:
                return None

            ringer = Ringer()
            for result in results:
                ringer_name = cls._RingerName(*result)
                if ringer_name.link_id and not ringer_name.date_to:
                    ringer.__aliases.append(ringer_name)
                else:
                    ringer.__names.append(ringer_name)

            return Cache.get_cache().add(cls.__name__, id, ringer)

    @classmethod
    def get_by_name(cls,
                    last_name: str = None,
                    given_names: str = None,
                    is_composer: bool = None,
                    date: datetime = None,
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
        date_clause = ''
        params = {}
        if last_name:
            name_clause += f'AND @tbl.last_name {"=" if exact_match else "LIKE"} %(last_name)s '
            params['last_name'] = last_name.strip()
        elif exact_match:
            name_clause += 'AND @tbl.last_name IS NULL '
        if given_names:
            # Strip internal spaces when matching as initials vary in format
            name_clause += 'AND REPLACE(@tbl.given_names, " ", "") LIKE %(given_names)s '
            params['given_names'] = given_names.strip().replace(' ', '')
        elif exact_match:
            name_clause += 'AND @tbl.given_names IS NULL '
        if is_composer is not None:
            name_clause += 'AND @tbl.is_composer = %(is_composer)s '
            params['is_composer'] = is_composer
        if date:
            date_clause += 'AND (@tbl.date_to IS NULL OR @tbl.date_to >= %(date)s) '
            params['date'] = date

        results = Database.get_connection().query(
            'SELECT id FROM ringers AS r ' +
            f'WHERE 1=1 {name_clause.replace("@tbl", "r")} AND r.link_id IS NULL ' +
            'OR (r.id IN (SELECT lr.link_id FROM ringers AS lr ' +
            f'WHERE 1=1 {name_clause.replace("@tbl", "lr")} ' +
            f' {date_clause.replace("@tbl", "lr")}' +
            'AND lr.link_id IS NOT NULL))',
            params
        ).fetchall()
        return [cls.get(result[0]) for result in results]

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('DELETE FROM ringers WHERE link_id IS NOT NULL')
        Database.get_connection().query('DELETE FROM ringers WHERE id > 0')
        Database.get_connection().query('ALTER TABLE ringers AUTO_INCREMENT = 1')
        Database.get_connection().commit()
        Cache.get_cache().clear(cls.__name__)

    @dataclass
    class _RingerName():

        last_name: str
        given_names: str
        title: str
        is_composer: bool = False
        link_id: int = None
        date_to: datetime.date = None
        home_tower: Tower = None
        id: int = None

        def __init__(self,
                     last_name: str,
                     given_names: str,
                     title: str = None,
                     is_composer: bool = False,
                     link_id: int = None,
                     date_to: datetime.date = None,
                     home_tower_id: int = None,
                     id: int = None):
            self.last_name = last_name
            self.given_names = given_names
            self.title = title
            self.is_composer = is_composer
            self.link_id = link_id
            self.date_to = date_to
            self.home_tower = Tower.get(home_tower_id) if home_tower_id else None
            self.id = id

        @property
        def name(self) -> str:
            text = ''
            text += f'{self.title} ' if self.title else ''
            text += f'{self.given_names} ' if self.given_names else ''
            text += f'{self.last_name}' if self.last_name else ''
            return text if len(text) > 0 else None

        def matches(self, last_name: str, given_names: str) -> bool:
            return self.last_name.lower() == last_name.lower() \
                   and (self.given_names or '').lower() == (given_names or '').lower()

        def commit(self):
            if self.id:
                result = Database.get_connection().query(
                    'UPDATE ringers ' +
                    'SET last_name = %s, given_names = %s, title = %s, is_composer = %s, link_id = %s, date_to = %s, home_tower_id = %s ' +
                    'WHERE id = %s',
                    (self.last_name, self.given_names, self.title, self.is_composer, self.link_id, self.date_to,
                     self.home_tower.id if self.home_tower else None, self.id))
                Database.get_connection().commit()
            else:
                result = Database.get_connection().query(
                    f'INSERT INTO ringers ({",".join(FIELD_LIST)}) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (self.last_name, self.given_names, self.title, self.is_composer, self.link_id, self.date_to,
                     self.home_tower.id if self.home_tower else None))
                Database.get_connection().commit()
                self.id = result.lastrowid
