from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pypeal.cache import Cache
from pypeal.db import Database
from pypeal.entities.peal import Peal
from pypeal.entities.ringer import Ringer
from pypeal.entities.tower import Ring, Tower

FIELD_LIST: list[str] = ['name', 'ringer_id', 'tower_id', 'ring_id', 'date_from', 'date_to', 'created_date']


@dataclass
class Report():

    name: str
    ringer: Ringer
    tower: Tower
    ring: Ring
    date_from: datetime.date
    date_to: datetime.date
    created_date: datetime
    id: int

    def __init__(self,
                 name: str = None,
                 ringer_id: int = None,
                 tower_id: int = None,
                 ring_id: int = None,
                 date_from: datetime.date = None,
                 date_to: datetime.date = None,
                 created_date: datetime = None,
                 id: int = None):
        self.name = name
        self.ringer = Ringer.get(ringer_id) if ringer_id else None
        self.tower = Tower.get(tower_id) if tower_id else None
        self.ring = Ring.get(ring_id) if ring_id else None
        self.date_from = date_from
        self.date_to = date_to
        self.created_date = created_date
        self.id = id

    def __str__(self) -> str:
        return self.name or 'Unnamed report'

    def commit(self):

        if self.id:
            Database.get_connection().query(
                f'UPDATE reports SET {",".join([f"{field} = %s" for field in FIELD_LIST])} WHERE id = %s',
                params=(self.name, self.ringer.id if self.ringer else None, self.tower.id if self.tower else None,
                        self.ring.id if self.ring else None, self.date_from, self.date_to, self.created_date, self.id))
            Database.get_connection().commit()
        else:
            self.created_date = self.last_run_date = datetime.now()
            result = Database.get_connection().query(
                f'INSERT INTO reports ({",".join(FIELD_LIST)}) ' +
                f'VALUES ({("%s,"*len(FIELD_LIST)).strip(",")})',
                (self.name, self.ringer.id if self.ringer else None, self.tower.id if self.tower else None,
                 self.ring.id if self.ring else None, self.date_from, self.date_to, self.created_date))
            Database.get_connection().commit()
            self.id = result.lastrowid
            Cache.get_cache().add(self.__class__.__name__, self.id, self)

    def get_peals(self) -> list[Peal]:
        return Peal.search(date_from=self.date_from,
                           date_to=self.date_to,
                           ring_id=self.ring.id if self.ring else None,
                           tower_id=self.tower.id if self.tower else None,
                           ringer_id=self.ringer.id if self.ringer else None)

    def delete(self):
        Database.get_connection().query('DELETE FROM reports WHERE id = %s', (self.id,))
        Database.get_connection().commit()
        Cache.get_cache().clear(self.__class__.__name__, self.id)

    @classmethod
    def get_all(cls) -> list[Report]:
        results = Database.get_connection().query(f'SELECT {",".join(FIELD_LIST)}, id FROM reports').fetchall()
        return Cache.get_cache().add_all(cls.__name__, {result[-1]: Report(*result) for result in results})

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE reports')
        Database.get_connection().commit()
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
        Cache.get_cache().clear(cls.__name__)
