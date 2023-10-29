from __future__ import annotations
from dataclasses import dataclass
import logging
from typing import ClassVar
from pypeal.db import Database

_logger = logging.getLogger('pypeal')

FIELD_LIST: list[str] = ['towerbase_id', 'place', 'sub_place', 'dedication', 'county', 'country', 'country_code', 'latitude', 'longitude',
                         'bells', 'tenor_weight', 'tenor_note']


@dataclass
class Tower:

    __cache_by_dove_id: ClassVar[dict[int, Tower]] = {}
    __cache_by_towerbase_id: ClassVar[dict[int, Tower]] = {}

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
        if self.tenor_weight is None:
            return 'Unknown'
        cwt = self.tenor_weight // 112
        lbs = self.tenor_weight % 112
        if lbs / 112 > 0.75:
            qtr = 3
        elif lbs / 112 > 0.5:
            qtr = 2
        elif lbs / 112 > 0.25:
            qtr = 1
        else:
            qtr = 0
        lbs -= qtr * 28
        if qtr == lbs == 0:
            return f'{self.tenor_weight // 112} cwt'
        else:
            return f'{cwt}-{qtr}-{lbs}'

    def __str__(self):
        text = ''
        text += self.place or ''
        text += f', {self.sub_place}' if self.sub_place else ''
        text += f', {self.county}' if self.county else ''
        text += f', {self.country}' if self.country else ''
        text += f', {self.dedication}' if self.dedication else ''
        text += '.'
        text += f'{self.bells}, ' if self.bells else ''
        text += f'{self.tenor_weight_in_cwt} ' if self.tenor_weight else ''
        text += f'in {self.tenor_note}' if self.tenor_note else ''
        text += '.'
        return text

    @classmethod
    def get(cls, dove_id: int = None, towerbase_id: int = None) -> Tower:
        if (tower := cls.__from_cache(dove_id=dove_id, towerbase_id=towerbase_id)) is not None:
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
            return cls.__cache_result(result)

    @classmethod
    def get_all(cls) -> list[Tower]:
        results = Database.get_connection().query(
            f'SELECT {",".join(FIELD_LIST)}, id ' +
            'FROM towers').fetchall()
        return cls.__cache_results(results)

    def commit(self):
        Database.get_connection().query(
            f'INSERT INTO towers ({",".join(FIELD_LIST)}, id) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (self.towerbase_id, self.place, self.sub_place, self.dedication, self.county, self.country, self.country_code, self.latitude,
             self.longitude, self.bells, self.tenor_weight, self.tenor_note, self.id))
        Database.get_connection().commit()

    @classmethod
    def __cache_result(cls, result: tuple) -> Tower:
        if result is None:
            return None
        tower = Tower(*result)
        if tower.id not in cls.__cache_by_dove_id:
            cls.__cache_by_dove_id[tower.id] = tower
            cls.__cache_by_towerbase_id[tower.towerbase_id] = tower
        return cls.__cache_by_dove_id[tower.id]

    @classmethod
    def __from_cache(cls, dove_id: int, towerbase_id: int) -> Tower:
        if dove_id is not None and dove_id in cls.__cache_by_dove_id:
            return cls.__cache_by_dove_id[dove_id]
        if towerbase_id is not None and towerbase_id in cls.__cache_by_towerbase_id:
            return cls.__cache_by_towerbase_id[towerbase_id]
        return None

    @classmethod
    def __cache_results(cls, results: list[tuple]) -> list[Tower]:
        return [cls.__cache_result(tower) for tower in results]
