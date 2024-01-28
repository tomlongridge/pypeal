from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import logging
from pypeal import utils
from pypeal.cache import Cache
from pypeal.db import Database
from pypeal import config


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

    @property
    def rings(self) -> list[Ring]:
        results = Database.get_connection().query(
            'SELECT id FROM rings ' +
            'WHERE tower_id = %s ' +
            'ORDER BY -date_removed DESC',
            (self.id,)).fetchall()
        return [Ring.get(result[0]) for result in results]

    def get_active_ring(self, at_date: datetime.date = datetime.now()) -> Ring:
        results = Database.get_connection().query(
            'SELECT id FROM rings ' +
            'WHERE tower_id = %s ' +
            'AND (date_removed IS NULL OR date_removed > %s) ' +
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
        default_country_name = config.get_config('general', 'default_country_name')
        if self.country and (not default_country_name or self.country.lower() != default_country_name.lower()):
            text += f', {self.country}'
        text += f', {self.dedication}' if self.dedication else ''
        return text

    def get_peals(self):
        from pypeal.entities.peal import Peal
        ring_ids = ','.join([str(ring.id) for ring in self.rings])
        results = Database.get_connection().query(
            'SELECT id FROM peals WHERE ring_id IN (%s) ',
            (ring_ids,)).fetchall()
        return [Peal.get(result[0]) for result in results]

    def __str__(self):
        text = self.name
        text += '. '
        text += f'{self.bells}, ' if self.bells else ''
        text += f'{self.tenor_weight_in_cwt} ' if self.tenor_weight else ''
        text += f'in {self.tenor_note}' if self.tenor_note else ''
        text += '.'
        return text

    def __hash__(self) -> int:
        return self.id

    def commit(self):
        Database.get_connection().query(
            f'INSERT INTO towers ({",".join(FIELD_LIST)}, id) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (self.towerbase_id, self.place, self.sub_place, self.dedication, self.county, self.country, self.country_code, self.latitude,
             self.longitude, self.bells, self.tenor_weight, self.tenor_note, self.id))
        Database.get_connection().commit()
        Cache.get_cache().add(self.__class__.__name__, f'D{self.id}', self)
        Cache.get_cache().add(self.__class__.__name__, f'T{self.towerbase_id}', self)

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

    @classmethod
    def search(cls,
               place: str = None,
               dedication: str = None,
               county: str = None,
               country: str = None,
               country_code: str = None,
               num_bells: int = None,
               exact_match: bool = False,
               limit: int = 30) -> list[Tower]:

        if exact_match:
            if place and '%' in place:
                raise ValueError('Exact match specified in method search, but place contains wildcard')
        else:
            place = f'{place}%' if place and '%' not in place else place

        query = f'SELECT {",".join(FIELD_LIST)}, id FROM towers WHERE 1=1 '
        params = {}
        if place:
            if exact_match:
                query += 'AND (place = %(place)s OR sub_place = %(place)s) '
            else:
                query += 'AND (place LIKE %(place)s OR sub_place LIKE %(place)s) '
            params['place'] = f'{place}'
        elif exact_match:
            query += 'AND place IS NULL '
        if dedication is not None:
            query += 'AND dedication = %(dedication)s '
            params['dedication'] = dedication
        if county is not None:
            query += 'AND county = %(county)s '
            params['county'] = county
        if country is not None:
            query += 'AND country = %(country)s '
            params['country'] = country
        elif country_code is not None:
            query += 'AND country_code = %(country_code)s '
            params['country_code'] = country_code
        if num_bells is not None:
            query += 'AND bells = %(num_bells)s '
            params['num_bells'] = num_bells
        query += 'ORDER BY '
        query += '(SELECT COUNT(*) FROM peals LEFT JOIN rings ON rings.id = peals.ring_id ' + \
                 ' WHERE rings.tower_id = towers.id) DESC, ' + \
                 'towers.country, towers.county, towers.place, towers.sub_place, towers.dedication ASC '
        query += 'LIMIT %(limit)s'
        params['limit'] = limit

        results = Database.get_connection().query(query, params).fetchall()
        return Cache.get_cache().add_all(cls.__name__, {result[-1]: Tower(*result) for result in results})

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE towers')
        Database.get_connection().commit()
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
        Cache.get_cache().clear(cls.__name__)


@dataclass
class Ring():

    tower: Tower = None
    description: str = None
    date_removed: datetime.date = None
    id: int = None

    __bells: dict[int, Bell] = None
    __bells_by_id: dict[int, Bell] = None

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
            self.__bells_by_id = {}
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT rb.bell_id, rb.bell_role, IFNULL(rb.bell_weight, b.weight) AS weight, IFNULL(rb.bell_note, b.note) AS note ' +
                    'FROM ringbells rb ' +
                    'LEFT JOIN bells b ON rb.bell_id = b.id ' +
                    'WHERE ring_id = %s ' +
                    'ORDER BY bell_role ASC',
                    (self.id,)).fetchall()
                if not results:
                    _logger.debug(f'No bells found for ring {self.id}, adding bells from tower {self.tower.id}')
                    results = Database.get_connection().query(
                        'SELECT id, role, weight, note FROM bells ' +
                        'WHERE tower_id = %s ' +
                        'ORDER BY role ASC',
                        (self.tower.id,)).fetchall()
                for result in results:
                    bell = Bell.get(result[0])
                    # Overwrite tower's bell role, weight and note with ring's bell role
                    bell.role = result[1]
                    bell.weight = result[2]
                    bell.note = result[3]
                    self.__bells_by_id[int(result[0])] = bell
                    self.__bells[int(result[1])] = bell
        return self.__bells

    @property
    def num_bells(self) -> int:
        return len(self.bells)

    @property
    def tenor(self) -> Bell:
        return self.bells[list(self.bells.keys())[-1]]

    def get_bell(self, bell_num: int) -> Bell:
        return self.bells[bell_num]

    def get_bell_by_id(self, bell_id: int) -> Bell:
        self.bells  # ensure bells are loaded
        return self.__bells_by_id[bell_id]

    def add_bell(self, role: int, bell: Bell):
        self.bells[role] = bell
        self.__bells_by_id[bell.id] = bell

    def commit(self):
        result = Database.get_connection().query(
            f'INSERT INTO rings ({",".join(RING_FIELD_LIST)}) ' +
            'VALUES (%s, %s, %s)',
            (self.tower.id, self.description, self.date_removed))
        self.id = result.lastrowid
        Database.get_connection().query(
            'DELETE FROM ringbells WHERE ring_id = %s', (self.id,))
        for role, bell in self.bells.items():
            Database.get_connection().query(
                'INSERT INTO ringbells (ring_id, bell_id, bell_role) ' +
                'VALUES (%s, %s, %s)',
                (self.id, bell.id, role))
        Database.get_connection().commit()

    def get_peals(self):
        from pypeal.entities.peal import Peal
        results = Database.get_connection().query(
            'SELECT id FROM peals WHERE ring_id = %s ',
            (self.id,)).fetchall()
        return [Peal.get(result[0]) for result in results]

    def __hash__(self) -> int:
        return self.id

    @classmethod
    def get(cls, id: int) -> Ring:
        if (ring := Cache.get_cache().get(cls.__name__, id)) is not None:
            return ring
        else:
            result = Database.get_connection().query(
                f'SELECT {",".join(RING_FIELD_LIST)}, id ' +
                'FROM rings WHERE id = %s', (id,)).fetchone()
            return Cache.get_cache().add(cls.__name__, result[-1], Ring(*result)) if result else None

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE rings')
        Database.get_connection().commit()
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
        Cache.get_cache().clear(cls.__name__)


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

    def __hash__(self) -> int:
        return self.id

    @classmethod
    def get(cls, id: int) -> Bell:
        if (bell := Cache.get_cache().get(cls.__name__, id)) is not None:
            return bell
        else:
            result = Database.get_connection().query(
                f'SELECT {",".join(BELL_FIELD_LIST)}, id ' +
                'FROM bells WHERE id = %s', (id,)).fetchone()
            return Cache.get_cache().add(cls.__name__, result[-1], Bell(*result)) if result else None
