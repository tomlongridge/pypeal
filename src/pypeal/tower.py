from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import logging
from pypeal import utils
from pypeal.cache import Cache
from pypeal.db import Database

_logger = logging.getLogger('pypeal')

FIELD_LIST: list[str] = ['towerbase_id', 'place', 'sub_place', 'dedication', 'county', 'country', 'country_code', 'latitude', 'longitude',
                         'bells', 'tenor_weight', 'tenor_note']
RING_FIELD_LIST: list[str] = ['tower_id', 'description', 'date_removed']
BELL_FIELD_LIST: list[str] = ['tower_id', 'role', 'weight', 'note', 'cast_year', 'founder']


@dataclass
class Tower():

    towerbase_id: int = None
    place: str = None
    sub_place: str = None
    dedication: str = None
    county: str = None
    country: str = None
    country_code: str = None
    latitude: float = None
    longitude: float = None
    bells: int = None
    tenor_weight: int = None
    tenor_note: str = None
    id: int = None

    @property
    def tenor_weight_in_cwt(self) -> str:
        return utils.get_weight_str(self.tenor_weight)

    def get_active_ring(self, at_date: datetime.date) -> Ring:
        results = Database.get_connection().query(
            'SELECT id FROM rings ' +
            'WHERE tower_id = %s ' +
            'AND date_removed IS NULL OR date_removed > %s ' +
            'ORDER BY -date_removed DESC ' +
            'LIMIT 1',
            (self.id, at_date)).fetchone()
        if results:
            return Ring.get(results[0])
        else:
            _logger.debug(f'No active ring found for tower {self.id} at {at_date}, creating one')
            ring = Ring(tower_id=self.id, description=None, date_removed=None)
            ring.commit()
            return ring

    @property
    def name(self):
        text = self.place or ''
        text += f', {self.sub_place}' if self.sub_place else ''
        text += f', {self.county}' if self.county else ''
        text += f', {self.country}' if self.country else ''
        text += f', {self.dedication}' if self.dedication else ''
        return text

    def __str__(self):
        text = self.name
        text += '.'
        text += f'{self.bells}, ' if self.bells else ''
        text += f'{self.tenor_weight_in_cwt} ' if self.tenor_weight else ''
        text += f'in {self.tenor_note}' if self.tenor_note else ''
        text += '.'
        return text

    @classmethod
    def get(cls, dove_id: int = None, towerbase_id: int = None) -> Tower:
        if dove_id:
            key = f'D{dove_id}'
        elif towerbase_id:
            key = f'T{towerbase_id}'
        else:
            raise ValueError('Either dove_id or towerbase_id must be specified')
        if (tower := Cache.get_cache().get(cls.__name__, key)) is not None:
            return tower
        else:
            query = f'SELECT {",".join(FIELD_LIST)}, id FROM towers WHERE 1=1 '
            params = {}
            if dove_id is not None:
                query += 'AND id = %(id)s '
                params['id'] = dove_id
            if towerbase_id is not None:
                query += 'AND towerbase_id = %(towerbase_id)s '
                params['towerbase_id'] = towerbase_id

            result = Database.get_connection().query(query, params).fetchone()
            if result is None:
                return None

            tower = Tower(*result)
            Cache.get_cache().add(cls.__name__, f'D{tower.id}', tower)
            Cache.get_cache().add(cls.__name__, f'T{tower.towerbase_id}', tower)
            return tower

    def commit(self):
        Database.get_connection().query(
            f'INSERT INTO towers ({",".join(FIELD_LIST)}, id) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (self.towerbase_id, self.place, self.sub_place, self.dedication, self.county, self.country, self.country_code, self.latitude,
             self.longitude, self.bells, self.tenor_weight, self.tenor_note, self.id))
        Database.get_connection().commit()
        Cache.get_cache().add(self.__class__.__name__, f'D{self.id}', self)
        Cache.get_cache().add(self.__class__.__name__, f'T{self.towerbase_id}', self)


@dataclass
class Ring():

    tower: Tower = None
    description: str = None
    date_removed: datetime.date = None
    id: int = None

    __bells: dict[int, Bell] = None

    def __init__(self,
                 tower_id: int = None,
                 description: str = None,
                 date_removed: datetime.date = None,
                 id: int = None):
        self.tower = Tower.get(dove_id=tower_id) if tower_id else None
        self.description = description
        self.date_removed = date_removed
        self.id = id

    @property
    def bells(self) -> dict[int, Bell]:
        if self.__bells is None:
            self.__bells = {}
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT bell_id, bell_role FROM ringbells ' +
                    'WHERE ring_id = %s ' +
                    'ORDER BY bell_role ASC',
                    (self.id,)).fetchall()
                self.__bells = {int(result[1]): Bell.get(result[0]) for result in results}
                if len(self.__bells) == 0:
                    _logger.debug(f'No bells found for ring {self.id}, adding bells from tower {self.tower.id}')
                    results = Database.get_connection().query(
                        'SELECT id, role FROM bells ' +
                        'WHERE tower_id = %s ' +
                        'ORDER BY role ASC',
                        (self.tower.id,)).fetchall()
                    for result in results:
                        self.add_bell(result[1], Bell.get(result[0]))
        return self.__bells

    def add_bell(self, role: int, bell: Bell):
        self.bells[role] = bell

    def get_tenor_bell(self, tenor_bell_num: int) -> Bell:
        if tenor_bell_num <= len(self.bells):
            return self.bells[tenor_bell_num]
        else:
            return None

    def commit(self):
        result = Database.get_connection().query(
            f'INSERT INTO rings ({",".join(RING_FIELD_LIST)}) ' +
            'VALUES (%s, %s, %s)',
            (self.tower.id, self.description, self.date_removed))
        Database.get_connection().commit()
        self.id = result.lastrowid
        Database.get_connection().query(
            'DELETE FROM ringbells WHERE ring_id = %s', (self.id,))
        for role, bell in self.bells.items():
            Database.get_connection().query(
                'INSERT INTO ringbells (ring_id, bell_id, bell_role) ' +
                'VALUES (%s, %s, %s)',
                (self.id, bell.id, role))

    @classmethod
    def get(cls, id: int) -> Ring:
        if (ring := Cache.get_cache().get(cls.__name__, id)) is not None:
            return ring
        else:
            result = Database.get_connection().query(
                f'SELECT {",".join(RING_FIELD_LIST)}, id ' +
                'FROM rings WHERE id = %s', (id,)).fetchone()
            ring: Ring = Cache.get_cache().add(cls.__name__, result[-1], Ring(*result))
            return ring


@dataclass
class Bell():

    tower: Tower = None
    role: int = None
    weight: int = None
    note: str = None
    cast_year: int = None
    founder: str = None
    id: int = None

    def __init__(self,
                 tower_id: int = None,
                 role: int = None,
                 weight: int = None,
                 note: str = None,
                 cast_year: int = None,
                 founder: str = None,
                 id: int = None):
        self.tower = Tower.get(dove_id=tower_id) if tower_id else None
        self.role = role
        self.weight = weight
        self.note = note
        self.cast_year = cast_year
        self.founder = founder
        self.id = id

    @property
    def formatted_weight(self) -> str:
        return utils.get_weight_str(self.weight)

    def commit(self):
        Database.get_connection().query(
            f'INSERT INTO bells ({",".join(BELL_FIELD_LIST)}, id) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (self.tower.id, self.role, self.weight, self.note, self.cast_year, self.founder, self.id))
        Database.get_connection().commit()
        Cache.get_cache().add(self.__class__.__name__, self.id, self)

    @classmethod
    def get(cls, id: int) -> Bell:
        if (bell := Cache.get_cache().get(cls.__name__, id)) is not None:
            return bell
        else:
            result = Database.get_connection().query(
                f'SELECT {",".join(BELL_FIELD_LIST)}, id ' +
                'FROM bells WHERE id = %s', (id,)).fetchone()
            return Cache.get_cache().add(cls.__name__, result[-1], Bell(*result))
