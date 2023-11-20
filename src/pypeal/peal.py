from __future__ import annotations
import copy
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
from pypeal import config, utils
from pypeal.association import Association
from pypeal.cache import Cache
from pypeal.db import Database
from pypeal.method import Classification, Method, Stage
from pypeal.ringer import Ringer
from pypeal.tower import Bell, Ring
from pypeal.utils import format_date_full, get_bell_label

FIELD_LIST: list[str] = ['bellboard_id', 'type', 'bell_type', 'date', 'association_id', 'ring_id', 'place', 'sub_place', 'address',
                         'dedication', 'county', 'country', 'tenor_weight', 'tenor_note', 'changes', 'stage', 'classification',
                         'is_variable_cover', 'num_methods', 'num_principles', 'num_variants', 'method_id', 'title', 'published_title',
                         'detail', 'composer_id', 'composition_url', 'duration', 'event_url', 'muffles']


class PealType(Enum):
    SINGLE_METHOD = 1
    MIXED_METHODS = 2
    SPLICED_METHODS = 3
    GENERAL_RINGING = 0


class PealLengthType(Enum):
    TOUCH = 1
    QUARTER_PEAL = 2
    HALF_PEAL = 3
    PEAL = 4
    LONG_LENGTH = 5


class BellType(Enum):
    TOWER = 1
    HANDBELLS = 2


class MuffleType(Enum):
    HALF = 1
    FULL = 2


@dataclass
class Peal:

    bellboard_id: int
    type: PealType
    bell_type: BellType
    date: datetime.date
    association: Association
    ring: Ring
    address: str
    changes: int
    stage: Stage
    classification: Classification
    is_variable_cover: bool
    num_methods: int
    num_principles: int
    num_variants: int
    method: Method
    published_title: str
    detail: str
    composer: Ringer
    composition_url: str
    duration: int
    event_url: str
    muffles: MuffleType
    id: int

    __title: str

    # Fields shared with Tower
    __place: str
    __sub_place: str
    __county: str
    __country: str
    __dedication: str
    __tenor_weight: int
    __tenor_note: str

    __methods: list[tuple[Method, int]]

    __ringers: list[(Ringer, list[int], list[int], bool)]
    __ringers_by_id: dict[int, Ringer]
    __ringers_by_bell_num: dict[int, Ringer]

    __footnotes: list[(str, int)]

    def __init__(self,
                 bellboard_id: int = None,
                 type: int = None,
                 bell_type: int = None,
                 date: datetime.date = None,
                 association_id: int = None,
                 ring_id: int = None,
                 place: str = None,
                 sub_place: str = None,
                 address: str = None,
                 dedication: str = None,
                 county: str = None,
                 country: str = None,
                 tenor_weight: int = None,
                 tenor_note: str = None,
                 changes: int = None,
                 stage: int = None,
                 classification: str = None,
                 is_variable_cover: bool = False,
                 num_methods: int = None,
                 num_principles: int = None,
                 num_variants: int = None,
                 method_id: int = None,
                 title: str = None,
                 published_title: str = None,
                 detail: str = None,
                 composer_id: int = None,
                 composition_url: str = None,
                 duration: int = None,
                 event_url: str = None,
                 muffles: int = None,
                 id: int = None):
        self.bellboard_id = bellboard_id
        self.bell_type = BellType(bell_type) if bell_type else None
        self.type = PealType(type) if type is not None else None
        self.date = date
        self.association = Association.get(association_id) if association_id else None
        self.ring = Ring.get(ring_id) if ring_id else None
        self.__place = place
        self.__sub_place = sub_place
        self.address = address
        self.__dedication = dedication
        self.__county = county
        self.__country = country
        self.changes = changes
        self.__tenor_weight = tenor_weight
        self.__tenor_note = tenor_note
        self.stage = Stage(stage) if stage else None
        self.classification = Classification(classification) if classification else None
        self.is_variable_cover = is_variable_cover
        self.num_methods = num_methods
        self.num_principles = num_principles
        self.num_variants = num_variants
        self.method = Method.get(method_id) if method_id else None
        self.__title = title
        self.published_title = published_title
        self.detail = detail
        self.composer = Ringer.get(composer_id) if composer_id else None
        self.composition_url = composition_url
        self.duration = duration
        self.event_url = event_url
        self.muffles = MuffleType(muffles) if muffles else None
        self.id = id

        self.__methods = None

        self.__ringers = None
        self.__ringers_by_id = None
        self.__ringers_by_bell_num = None

        self.__footnotes = None

    @property
    def place(self) -> str:
        if self.__place:
            return self.__place
        elif self.ring:
            return self.ring.tower.place
        else:
            return None

    @place.setter
    def place(self, value: str):
        self.__place = value

    @property
    def sub_place(self) -> str:
        if self.__sub_place:
            return self.__sub_place
        elif self.ring:
            return self.ring.tower.sub_place
        else:
            return None

    @sub_place.setter
    def sub_place(self, value: str):
        self.__sub_place = value

    @property
    def county(self) -> str:
        if self.__county:
            return self.__county
        elif self.ring:
            return self.ring.tower.county
        else:
            return None

    @county.setter
    def county(self, value: str):
        self.__county = value

    @property
    def country(self) -> str:
        if self.__country:
            return self.__country
        elif self.ring:
            return self.ring.tower.country
        else:
            return None

    @country.setter
    def country(self, value: str):
        self.__country = value

    @property
    def dedication(self) -> str:
        if self.__dedication:
            return self.__dedication
        elif self.ring:
            return self.ring.tower.dedication
        else:
            return None

    @dedication.setter
    def dedication(self, value: str):
        self.__dedication = value

    @property
    def tenor(self) -> Bell:
        if self.ring and len(self.ringers) > 0 and self.ringers[-1][2]:
            largest_bell_num_rung = self.ringers[-1][2][-1]
            return self.ring.get_bell(largest_bell_num_rung)
        return None

    @property
    def tenor_weight(self) -> int:
        if self.__tenor_weight:
            return self.__tenor_weight
        elif self.tenor:
            return self.tenor.weight
        else:
            return None

    @tenor_weight.setter
    def tenor_weight(self, value: int):
        self.__tenor_weight = value

    @property
    def tenor_note(self) -> str:
        if self.__tenor_note:
            return self.__tenor_note
        if self.ring and self.tenor:
            return self.tenor.note
        else:
            return None

    @tenor_note.setter
    def tenor_note(self, value: str):
        self.__tenor_note = value

    @property
    def tenor_description(self) -> str:
        if self.tenor_weight:
            text = utils.get_weight_str(self.tenor_weight)
            if self.tenor_note:
                text += f' in {self.tenor_note}'
            return text
        return None

    @property
    def location(self) -> str:
        text = ''
        text += f'{self.place}' if self.place else ''
        text += f', {self.county}' if self.county else ''
        text += f', {self.country}' if self.country else ''
        return text if len(text) > 0 else None

    @property
    def location_detail(self) -> str:
        text = ''
        text += f'{self.address}' if self.address else ''
        text += f'{self.dedication}' if self.dedication else ''
        text += f', {self.sub_place}' if self.sub_place else ''
        return text if len(text) > 0 else None

    @property
    def methods(self) -> list[tuple[Method, int]]:
        if self.__methods is None:
            self.__methods = []
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT method_id, changes FROM pealmethods WHERE peal_id = %s', (self.id,)).fetchall()
                for method_id, changes in results:
                    self.__methods.append((Method.get(method_id), changes))
        return self.__methods

    def add_method(self, method: Method, changes: int = None):
        if method is not None:
            self.methods.append((method, changes))

    def clear_methods(self):
        self.__methods = None

    @property
    def num_methods_in_title(self) -> int:
        return (self.num_methods or 0) + (self.num_variants or 0) + (self.num_principles or 0)

    @property
    def length_type(self) -> PealLengthType:
        if self.changes is None:
            return None
        elif config.get_config('general', 'allow_short_quarter_peals_under_triples') or (self.stage and self.stage.value < 7):
            if self.changes < 1250:
                return PealLengthType.TOUCH
            elif self.changes < 5000:
                return PealLengthType.QUARTER_PEAL
        else:
            if self.changes < 1260:
                return PealLengthType.TOUCH
            elif self.changes < 5040:
                return PealLengthType.QUARTER_PEAL
        if self.changes < 10_000:
            return PealLengthType.PEAL
        else:
            return PealLengthType.LONG_LENGTH

    @property
    def title(self) -> str:
        if self.method:
            if self.method.full_name:
                return self.method.full_name
            if self.method.title:
                return self.method.title
        text = ''
        text += 'Spliced ' if self.type == PealType.SPLICED_METHODS else ''
        text += 'Mixed ' if self.type == PealType.MIXED_METHODS else ''
        text += f'{self.classification.value} ' if self.classification else ''
        if self.stage and self.is_variable_cover and self.stage.value % 2 == 0:
            text += f'{Stage(self.stage.value - 1).name.capitalize()} and '
        text += f'{self.stage.name.capitalize()} ' if self.stage else ''
        if self.stage and self.is_variable_cover and self.stage.value % 2 == 1:
            text += f'and {Stage(self.stage.value + 1).name.capitalize()} '
        if self.num_methods_in_title > 0:
            text += '('
            text += f'{self.num_methods}m/' if self.num_methods else ''
            text += f'{self.num_variants}v/' if self.num_variants else ''
            text += f'{self.num_principles}p/' if self.num_principles else ''
            text = text.rstrip('/')
            text += ')'
        text = text.strip()
        if len(text) > 0:
            return text
        elif self.__title:
            return self.__title
        else:
            return 'Unknown'

    @title.setter
    def title(self, value: str):
        self.__title = value

    @property
    def ringers(self) -> list[tuple[Ringer, list[int], list[int], bool]]:
        if self.__ringers is None:
            self.__ringers = []
            self.__ringers_by_id = {}
            self.__ringers_by_bell_num = {}
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT r.id, pr.bell_num, pr.bell, pr.is_conductor ' +
                    'FROM pealringers pr ' +
                    'JOIN ringers r ON pr.ringer_id = r.id ' +
                    'WHERE pr.peal_id = %s ' +
                    'ORDER BY pr.bell ASC',
                    (self.id,)).fetchall()
                last_ringer = None
                for ringer_id, bell_num, bell, is_conductor in results:
                    if ringer_id == last_ringer:
                        self.__ringers[-1][1].append(bell_num)
                        self.__ringers[-1][2].append(bell)
                    else:
                        ringer = Ringer.get(ringer_id)
                        if bell == 0:  # 0 means no particular bell, for general performances
                            self.__ringers.append((ringer, None, None, is_conductor))
                        else:
                            self.__ringers.append((ringer, [bell_num], [bell], is_conductor))
                            self.__ringers_by_bell_num[bell_num] = ringer
                            self.__ringers_by_id[ringer_id] = ringer
                    last_ringer = ringer_id
        return self.__ringers

    def get_ringer(self, bell_num: int) -> Ringer:
        if bell_num in self.__ringers_by_bell_num:
            return self.__ringers_by_bell_num[bell_num]
        else:
            return None

    def get_ringer_line(self, ringer: (Ringer, list[int], list[int], bool)) -> str:
        text = ''
        if ringer[1]:
            text += get_bell_label(ringer[1])
            if ringer[1] != ringer[2]:
                text += f' [{get_bell_label(ringer[2])}]'
            text += ': ' if ringer[2] else ''
        text += str(ringer[0])
        if ringer[3]:
            text += " (c)"
        return text

    def add_ringer(self, ringer: Ringer, bell_nums: list[int] = None, bells: list[int] = None, is_conductor: bool = False):
        self.ringers.append((ringer, bell_nums, bells, is_conductor))
        if ringer.id and ringer.id in self.__ringers_by_id:
            self.__ringers_by_id[ringer.id] = ringer
        if bell_nums is not None:
            for bell in bell_nums:
                self.__ringers_by_bell_num[bell] = ringer

    def clear_ringers(self):
        self.__ringers = None
        self.__ringers_by_id = None
        self.__ringers_by_bell_num = None

    @property
    def conductors(self) -> list[tuple[Ringer, list[int]]]:
        conductor_list = []
        for ringer in self.ringers:
            if ringer[3]:
                conductor_list.append((ringer[0], ringer[1]))
        return conductor_list

    @property
    def num_bells(self) -> int:
        return sum([len(ringer[1]) if ringer[1] else 0 for ringer in self.ringers])

    @property
    def footnotes(self) -> list[tuple[str, int, Ringer]]:
        if self.__footnotes is None:
            self.__footnotes = []
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT text, bell, ringer_id FROM pealfootnotes WHERE peal_id = %s', (self.id,)).fetchall()
                for footnote, bell, ringer_id in results:
                    self.__footnotes.append((footnote, bell, Ringer.get(ringer_id) if ringer_id else None))
        return self.__footnotes

    def add_footnote(self, footnote: str, bell: int, ringer: Ringer):
        self.footnotes.append((footnote, bell, ringer))

    def get_footnote_line(self, footnote: (str, int, Ringer)) -> str:
        text = ''
        if footnote[1]:
            text += f'[{footnote[1]}: {footnote[2]}] '
        text += f'{footnote[0]}'
        return text

    def commit(self):
        if self.id is None:
            result = Database.get_connection().query(
                f'INSERT INTO peals ({",".join(FIELD_LIST)}) ' +
                f'VALUES ({("%s,"*len(FIELD_LIST)).strip(",")})',
                (self.bellboard_id, self.type.value, self.bell_type.value, self.date, self.association.id if self.association else None,
                 self.ring.id if self.ring else None, self.__place, self.__sub_place, self.address, self.dedication, self.__county,
                 self.__country, self.__tenor_weight, self.__tenor_note, self.changes, self.stage.value if self.stage else None,
                 self.classification.value if self.classification else None, self.is_variable_cover, self.num_methods, self.num_principles,
                 self.num_variants, self.method.id if self.method else None, self.title, self.published_title, self.detail,
                 self.composer.id if self.composer else None, self.composition_url, self.duration, self.event_url,
                 self.muffles.value if self.muffles else None))
            Database.get_connection().commit()
            self.id = result.lastrowid
            for method, changes in self.methods:
                Database.get_connection().query(
                    'INSERT INTO pealmethods (peal_id, method_id, changes) VALUES (%s, %s, %s)',
                    (self.id, method.id, changes))
            Database.get_connection().commit()
            for ringer, bell_nums, bells, is_conductor in self.ringers:
                if bells is None:
                    Database.get_connection().query(
                        'INSERT INTO pealringers (peal_id, ringer_id, is_conductor) VALUES (%s, %s, %s)',
                        (self.id, ringer.id, is_conductor))
                else:
                    for bell_num, bell in zip(bell_nums, bells):
                        Database.get_connection().query(
                            'INSERT INTO pealringers (peal_id, ringer_id, bell_num, bell, is_conductor) ' +
                            'VALUES (%s, %s, %s, %s, %s)',
                            (self.id, ringer.id, bell_num, bell, is_conductor))
            footnote_num = 1
            for footnote, bell, ringer in self.footnotes:
                Database.get_connection().query(
                    'INSERT INTO pealfootnotes (peal_id, footnote_num, bell, ringer_id, text) VALUES (%s, %s, %s, %s, %s)',
                    (self.id, footnote_num, bell, ringer.id if ringer else None, footnote))
                footnote_num += 1
            Database.get_connection().commit()
        else:
            raise NotImplementedError('Updating existing peals is not yet supported')

    def __str__(self):
        text = ''
        text += f'{self.association.name}\n' if self.association else ''
        text += f'{self.location}\n' if self.location else ''
        if self.location_detail:
            text += f'{self.location_detail}'
            if self.bell_type == BellType.HANDBELLS:
                text += ' (in hand)'
            text += '\n'
        text += f'On {format_date_full(self.date)}\n' if self.date else ''
        text += f'A {self.length_type.name.replace("_", " ").title()} of ' if self.length_type else ''
        text += f'{self.changes} ' if self.changes else ''
        text += self.title
        text += ' (half-muffled)' if self.muffles == MuffleType.HALF else ''
        text += ' (muffled)' if self.muffles == MuffleType.FULL else ''
        text += ' '
        text += f'in {utils.get_time_str(self.duration)} ' if self.duration else ''
        text += f'({self.tenor_description})' if self.tenor_description else ''
        text += '\n'
        if len(self.methods) > 0:
            text += '('
            for method, changes in self.methods:
                text += f'{changes} ' if changes else ''
                text += f'{method.title}, '
            text = text.rstrip(', ')
            text += ')\n'
        text += f'{self.detail}\n' if self.detail else ''
        text += f'Composed by: {self.composer}\n' if self.composer else ''
        text += '\n'
        for ringer in self.ringers:
            text += f'{self.get_ringer_line(ringer)}\n'
        text += '\n' if len(self.footnotes) else ''
        for footnote in self.footnotes:
            text += self.get_footnote_line(footnote)
            text += '\n'
        text += '\n'
        text += f'[Imported Bellboard peal ID: {self.bellboard_id}]'
        text += f'\n[Composition URL: {self.composition_url}]' if self.composition_url else ''
        text += f'\n[Event URL: {self.event_url}]' if self.event_url else ''
        text += f'\n[Published title: {self.published_title}]' if self.published_title != self.title else ''
        return text

    def to_json(self):
        json_fields = {}
        return json.dumps(json_fields)

    def copy(self):
        return copy.deepcopy(self)

    @classmethod
    def get(cls, id: int = None, bellboard_id: int = None) -> Peal:
        if id:
            key = f'D{id}'
        elif bellboard_id:
            key = f'B{bellboard_id}'
        else:
            raise ValueError('Either database or BellBoard ID must be specified')
        if id is None and bellboard_id is None:
            raise ValueError('Either peal database ID or Bellboard ID must be specified')
        if (peal := Cache.get_cache().get(cls.__name__, key)) is not None:
            return peal
        else:
            result = Database.get_connection().query(
                f'SELECT {",".join(FIELD_LIST)}, id ' +
                'FROM peals ' +
                'WHERE true ' +
                ('AND id = %s ' if id else '') +
                ('AND bellboard_id = %s ' if bellboard_id else ''),
                (key,)).fetchone()

        if result is None:
            return None

        peal = Peal(*result)
        Cache.get_cache().add(cls.__name__, f'D{peal.id}', peal)
        Cache.get_cache().add(cls.__name__, f'B{peal.bellboard_id}', peal)
        return peal

    @classmethod
    def search(cls,
               ringer_name: str = None,
               date_from: datetime.date = None,
               date_to: datetime.date = None,
               tower_id: int = None,
               place: str = None,
               county: str = None,
               dedication: str = None,
               association: str = None,
               title: str = None,
               bell_type: BellType = None,
               order_descending: bool = True) -> list[Peal]:

        query = f'SELECT {",".join(["peals."+field for field in FIELD_LIST])}, peals.id ' + \
                'FROM peals ' + \
                'LEFT JOIN pealringers pr ON peals.id = pr.peal_id ' + \
                'LEFT JOIN ringers r ON pr.ringer_id = r.id ' + \
                'LEFT JOIN rings ri ON peals.ring_id = ri.id ' + \
                'LEFT JOIN towers t ON ri.tower_id = t.id ' + \
                'LEFT JOIN associations a ON peals.association_id = a.id ' + \
                'WHERE 1=1 '
        params = {}
        if ringer_name:
            query += 'AND CONCAT(r.given_names, " ", r.last_name) LIKE %(ringer_name)s '
            params['name'] = f'%{ringer_name}%'
        if date_from is not None:
            query += 'AND peals.date >= %(date_from)s '
            params['date_from'] = date_from.strftime('%Y-%m-%d')
        if date_to is not None:
            query += 'AND peals.date >= %(date_to)s '
            params['date_to'] = date_to.strftime('%Y-%m-%d')
        if tower_id is not None:
            query += 'AND ri.tower_id = %(tower_id)s '
            params['tower_id'] = tower_id
        if place is not None:
            query += 'AND (' + \
                     '(peals.place LIKE %(place)s) OR ' + \
                     '(peals.sub_place LIKE %(place)s) OR ' + \
                     '(t.place LIKE %(place)s) OR ' + \
                     '(t.sub_place LIKE %(place)s)' + \
                     ')'
            params['place'] = place
        if county is not None:
            query += 'AND (' + \
                     '(peals.county LIKE %(county)s) OR ' + \
                     '(t.county LIKE %(county)s) OR ' + \
                     ')'
            params['county'] = county
        if dedication is not None:
            query += 'AND (' + \
                     '(peals.dedication LIKE %(dedication)s) OR ' + \
                     '(t.dedication LIKE %(dedication)s) OR ' + \
                     ')'
            params['dedication'] = dedication
        if association is not None:
            query += 'AND a.name = %(association)s '
            params['association'] = association
        if title is not None:
            query += 'AND peals.title LIKE %(title)s '
            params['title'] = f'%{title}%'
        if bell_type is not None:
            query += 'AND peals.bell_type = %(bell_type)s '
            params['bell_type'] = bell_type.value
        query += 'ORDER BY peals.date ' + ('DESC' if order_descending else 'ASC')
        results = Database.get_connection().query(query, params).fetchall()
        cached_peals = Cache.get_cache().add_all(cls.__name__, {f'D{result[-1]}': Peal(*result) for result in results})
        return Cache.get_cache().add_all(cls.__name__, {f'B{peal.bellboard_id}': peal for peal in cached_peals})

    @classmethod
    def get_all(cls) -> list[Peal]:
        results = Database.get_connection().query(f'SELECT {",".join(FIELD_LIST)}, id FROM peals').fetchall()
        cached_peals = Cache.get_cache().add_all(cls.__name__, {f'D{result[-1]}': Peal(*result) for result in results})
        return Cache.get_cache().add_all(cls.__name__, {f'B{peal.bellboard_id}': peal for peal in cached_peals})

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE pealfootnotes')
        Database.get_connection().query('TRUNCATE TABLE pealringers')
        Database.get_connection().query('TRUNCATE TABLE pealmethods')
        Database.get_connection().query('TRUNCATE TABLE peals')
        Database.get_connection().commit()
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
