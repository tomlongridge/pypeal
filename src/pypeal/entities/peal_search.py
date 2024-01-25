from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pypeal.cache import Cache
from pypeal.db import Database

from pypeal.entities.peal import BellType

FIELD_LIST: list[str] = ['name', 'date_from', 'date_to', 'association', 'tower_id', 'place', 'county', 'dedication', 'title', 'bell_type',
                         'order_by_submission_date', 'order_descending']


@dataclass
class PealSearch():

    name: str = None
    date_from: datetime.date = None
    date_to: datetime.date = None
    association: str = None
    tower_id: int = None
    place: str = None
    county: str = None
    dedication: str = None
    title: str = None
    bell_type: BellType = None
    order_by_submission_date: bool = True
    order_descending: bool = True

    def commit(self):
        result = Database.get_connection().query(
            f'INSERT INTO pealsearches ({",".join(FIELD_LIST)}) ' +
            f'VALUES ({("%s,"*len(FIELD_LIST)).strip(",")})',
            (self.name, self.date_from, self.date_to, self.association, self.tower_id, self.place, self.county, self.dedication, self.title,
             self.bell_type, self.order_by_submission_date, self.order_descending))
        Database.get_connection().commit()
        self.id = result.lastrowid
        Cache.get_cache().add(self.__class__.__name__, self.id, self)

    def delete(self):
        Database.get_connection().query('DELETE FROM pealsearches WHERE id = %s', (self.id,))
        Cache.get_cache().clear(self.__class__.__name__, self.id)

    @classmethod
    def get_all(cls) -> list[PealSearch]:
        results = Database.get_connection().query(f'SELECT {",".join(FIELD_LIST)}, id FROM pealsearches').fetchall()
        return Cache.get_cache().add_all(cls.__name__, {result[-1]: PealSearch(*result) for result in results})
