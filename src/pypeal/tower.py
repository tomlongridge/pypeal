from __future__ import annotations
from dataclasses import dataclass
import logging
from typing import ClassVar
from pypeal.db import Database

_logger = logging.getLogger('pypeal')

FIELD_LIST: list[str] = ['place', 'place_2', 'dedication', 'county', 'country', 'country_code', 'latitude', 'longitude', 'bells',
                         'tenor_weight', 'tenor_note']


@dataclass
class Tower:

    __cache: ClassVar[dict[int, Tower]] = {}

    place: str = None
    place_2: str = None
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
        text += f', {self.place_2}' if self.place_2 else ''
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
    def get(cls, id: int) -> Tower:
        if id not in cls.__cache:
            result = Database.get_connection().query(
                f'SELECT {",".join(FIELD_LIST)}, id ' +
                'FROM towers WHERE id = %s', (id,)).fetchone()
            cls.__cache[id] = Tower(*result)
        return cls.__cache[id]

    @classmethod
    def get_all(cls) -> list[Tower]:
        results = Database.get_connection().query(
            f'SELECT {",".join(FIELD_LIST)}, id ' +
            'FROM towers').fetchall()
        return cls.__with_cache([Tower(*result) for result in results])

    def commit(self):
        Database.get_connection().query(
            f'INSERT INTO towers ({",".join(FIELD_LIST)}, id) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (self.place, self.place_2, self.dedication, self.county, self.country, self.country_code, self.latitude, self.longitude,
             self.bells, self.tenor_weight, self.tenor_note, self.id))
        Database.get_connection().commit()

    @classmethod
    def __with_cache(cls, results: list[Tower]) -> list[Tower]:
        towers = []
        for tower in results:
            if tower.id not in cls.__cache:
                cls.__cache[tower.id] = tower
            towers.append(cls.__cache[tower.id])
        return towers
