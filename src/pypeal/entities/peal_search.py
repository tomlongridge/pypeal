from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pypeal.cache import Cache
from pypeal.db import Database

from pypeal.entities.peal import BellType

FIELD_LIST: list[str] = ['description', 'ringer_name', 'date_from', 'date_to', 'association', 'tower_id', 'place', 'region', 'address',
                         'title', 'bell_type', 'order_by_submission_date', 'order_descending', 'poll', 'created_date', 'last_run_date']


@dataclass
class PealSearch():

    description: str
    ringer_name: str
    date_from: datetime.date
    date_to: datetime.date
    association: str
    tower_id: int
    place: str
    region: str
    address: str
    title: str
    bell_type: BellType
    order_by_submission_date: bool
    order_descending: bool
    poll: bool
    created_date: datetime
    last_run_date: datetime
    id: int

    def __init__(self,
                 description: str = None,
                 ringer_name: str = None,
                 date_from: datetime.date = None,
                 date_to: datetime.date = None,
                 association: str = None,
                 tower_id: int = None,
                 place: str = None,
                 region: str = None,
                 address: str = None,
                 title: str = None,
                 bell_type: BellType = None,
                 order_by_submission_date: bool = False,
                 order_descending: bool = False,
                 poll: bool = False,
                 created_date: datetime = None,
                 last_run_date: datetime = None,
                 id: int = None):
        self.description = description
        self.ringer_name = ringer_name
        self.date_from = date_from
        self.date_to = date_to
        self.association = association
        self.tower_id = tower_id
        self.place = place
        self.region = region
        self.address = address
        self.title = title
        self.bell_type = BellType(bell_type) if bell_type else None
        self.order_by_submission_date = order_by_submission_date
        self.order_descending = order_descending
        self.poll = poll
        self.created_date = created_date
        self.last_run_date = last_run_date
        self.id = id

    def __str__(self) -> str:
        return self.description or 'Unnamed search'

    def record_run(self):
        if self.id:
            self.last_run_date = datetime.now()
            Database.get_connection().query('UPDATE pealsearches SET last_run_date = %s WHERE id = %s',
                                            params=(self.last_run_date, self.id))
            Database.get_connection().commit()
            self.commit()

    def commit(self):

        if self.id:
            Database.get_connection().query(
                f'UPDATE pealsearches SET {",".join([f"{field} = %s" for field in FIELD_LIST])} WHERE id = %s',
                params=(self.description, self.ringer_name, self.date_from, self.date_to, self.association, self.tower_id, self.place,
                        self.region, self.address, self.title, self.bell_type.value if self.bell_type else None,
                        self.order_by_submission_date, self.order_descending, self.poll, self.created_date, self.last_run_date, self.id))
            Database.get_connection().commit()
        else:
            self.created_date = self.last_run_date = datetime.now()
            result = Database.get_connection().query(
                f'INSERT INTO pealsearches ({",".join(FIELD_LIST)}) ' +
                f'VALUES ({("%s,"*len(FIELD_LIST)).strip(",")})',
                (self.description, self.ringer_name, self.date_from, self.date_to, self.association, self.tower_id, self.place, self.region,
                 self.address, self.title, self.bell_type.value if self.bell_type else None, self.order_by_submission_date,
                 self.order_descending, self.poll, self.created_date, self.last_run_date))
            Database.get_connection().commit()
            self.id = result.lastrowid
            Cache.get_cache().add(self.__class__.__name__, self.id, self)

    def delete(self):
        Database.get_connection().query('DELETE FROM pealsearches WHERE id = %s', (self.id,))
        Database.get_connection().commit()
        Cache.get_cache().clear(self.__class__.__name__, self.id)

    @classmethod
    def get_all(cls) -> list[PealSearch]:
        results = Database.get_connection().query(f'SELECT {",".join(FIELD_LIST)}, id FROM pealsearches').fetchall()
        return Cache.get_cache().add_all(cls.__name__, {result[-1]: PealSearch(*result) for result in results})
