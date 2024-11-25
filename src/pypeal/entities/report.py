from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pypeal import utils
from pypeal.cache import Cache
from pypeal.db import Database
from pypeal.entities.association import Association
from pypeal.entities.peal import BellType, Peal, PealLengthType
from pypeal.entities.ringer import Ringer
from pypeal.entities.tower import Ring, Tower

FIELD_LIST: list[str] = ['name', 'ringer_id', 'tower_id', 'ring_id', 'association_id', 'date_from', 'date_to', 'length_type', 'bell_type',
                         'enabled', 'created_date', 'spreadsheet_id']


@dataclass
class Report():

    name: str
    ringer: Ringer
    tower: Tower
    ring: Ring
    association: Association
    date_from: datetime.date
    date_to: datetime.date
    length_type: PealLengthType
    bell_type: BellType
    enabled: bool
    created_date: datetime
    spreadsheet_id: str
    id: int

    def __init__(self,
                 name: str = None,
                 ringer_id: int = None,
                 tower_id: int = None,
                 ring_id: int = None,
                 association_id: int = None,
                 date_from: datetime.date = None,
                 date_to: datetime.date = None,
                 length_type: PealLengthType = None,
                 bell_type: BellType = None,
                 enabled: bool = None,
                 created_date: datetime = None,
                 spreadsheet_id: str = None,
                 id: int = None):
        self.name = name
        self.ringer = Ringer.get(ringer_id) if ringer_id else None
        self.tower = Tower.get(tower_id) if tower_id else None
        self.ring = Ring.get(ring_id) if ring_id else None
        self.association = Association.get(association_id) if association_id else None
        self.date_from = date_from
        self.date_to = date_to
        self.length_type = length_type
        self.bell_type = bell_type
        self.enabled = enabled
        self.created_date = created_date
        self.spreadsheet_id = spreadsheet_id
        self.id = id

    def __str__(self) -> str:
        return self.name or 'Unnamed report'

    def commit(self):

        if self.id:
            Database.get_connection().query(
                f'UPDATE reports SET {",".join([f"{field} = %s" for field in FIELD_LIST])} WHERE id = %s',
                params=(self.name, self.ringer.id if self.ringer else None, self.tower.id if self.tower else None,
                        self.ring.id if self.ring else None, self.association.id if self.association else None,
                        self.date_from, self.date_to, self.length_type.name if self.length_type else None,
                        self.bell_type.name if self.bell_type else None, self.enabled, self.created_date, self.spreadsheet_id, self.id))
            Database.get_connection().commit()
        else:
            self.created_date = self.last_run_date = utils.get_now()
            result = Database.get_connection().query(
                f'INSERT INTO reports ({",".join(FIELD_LIST)}) ' +
                f'VALUES ({("%s,"*len(FIELD_LIST)).strip(",")})',
                (self.name, self.ringer.id if self.ringer else None, self.tower.id if self.tower else None,
                 self.ring.id if self.ring else None, self.association.id if self.association else None, self.date_from, self.date_to,
                 self.length_type.name if self.length_type else None, self.bell_type.name if self.bell_type else None, self.enabled,
                 self.created_date, self.spreadsheet_id))
            Database.get_connection().commit()
            self.id = result.lastrowid
            Cache.get_cache().add(self.__class__.__name__, self.id, self)

    def get_peals(self, length_type: PealLengthType = None) -> list[Peal]:
        return Peal.search(date_from=self.date_from,
                           date_to=self.date_to,
                           ring_id=self.ring.id if self.ring else None,
                           tower_id=self.tower.id if self.tower else None,
                           association_id=self.association.id if self.association else None,
                           ringer_id=self.ringer.id if self.ringer else None,
                           length_type=length_type or self.length_type,
                           bell_type=self.bell_type)

    def delete(self):
        Database.get_connection().query('DELETE FROM reports WHERE id = %s', (self.id,))
        Database.get_connection().commit()
        Cache.get_cache().clear(self.__class__.__name__, self.id)

    @classmethod
    def get(cls, name: str) -> Report:
        result = Database.get_connection().query(
            f'SELECT {",".join(FIELD_LIST)}, id ' +
            'FROM reports ' +
            'WHERE name = %s', (name,)).fetchone()
        return Cache.get_cache().add(cls.__name__, result[-1], Report(*result)) if result else None

    @classmethod
    def get_all(cls, only_enabled: bool = True) -> list[Report]:
        query = f'SELECT {",".join(FIELD_LIST)}, id FROM reports'
        if only_enabled:
            query += ' WHERE enabled = 1'
        results = Database.get_connection().query(query).fetchall()
        return Cache.get_cache().add_all(cls.__name__, {result[-1]: Report(*result) for result in results})

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('DELETE FROM reports WHERE id > 0')
        Database.get_connection().query('ALTER TABLE reports AUTO_INCREMENT = 1')
        Database.get_connection().commit()
        Cache.get_cache().clear(cls.__name__)
