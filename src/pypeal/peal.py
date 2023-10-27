from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pypeal.db import Database
from pypeal.method import Method, Stage
from pypeal.ringer import Ringer
from pypeal.tower import Tower

PEAL_FIELD_LIST: list[str] = ['bellboard_id', 'type', 'date', 'association', 'tower_id', 'place', 'sub_place', 'address', 'dedication',
                              'county', 'country', 'tenor_weight', 'tenor_note', 'changes', 'stage', 'classification', 'is_spliced',
                              'is_mixed', 'is_variable_cover', 'num_methods', 'num_principles', 'num_variants', 'method_id', 'title',
                              'duration']


class PealType(Enum):
    TOWER = 1
    HANDBELLS = 2
    OTHER = 0


@dataclass
class Peal:

    bellboard_id: int
    type: PealType
    date: datetime.date
    association: str
    tower: Tower
    address: str
    changes: int
    stage: Stage
    classification: str
    is_spliced: bool
    is_mixed: bool
    is_variable_cover: bool
    num_methods: int
    num_principles: int
    num_variants: int
    method: Method
    title: str
    duration: int
    id: int

    # Fields shared with Tower
    __place: str
    __sub_place: str
    __county: str
    __country: str
    __dedication: str
    __tenor_weight: str
    __tenor_note: str

    __methods: list[tuple[Method, int]] = None

    __ringers: list[(Ringer, list[int], bool)] = None
    __ringers_by_id: dict[int, Ringer] = None
    __ringers_by_bell: dict[int, Ringer] = None

    __footnotes: list[(str, int)] = None

    def __init__(self,
                 bellboard_id: int = None,
                 type: int = PealType.TOWER,
                 date: datetime.date = None,
                 association: str = None,
                 tower_id: int = None,
                 place: str = None,
                 sub_place: str = None,
                 address: str = None,
                 dedication: str = None,
                 county: str = None,
                 country: str = None,
                 tenor_weight: str = None,
                 tenor_note: str = None,
                 changes: int = None,
                 stage: int = None,
                 classification: str = None,
                 is_spliced: bool = None,
                 is_mixed: bool = None,
                 is_variable_cover: bool = False,
                 num_methods: int = 0,
                 num_principles: int = 0,
                 num_variants: int = 0,
                 method_id: int = None,
                 title: str = None,
                 duration: int = None,
                 id: int = None):
        self.bellboard_id = bellboard_id
        self.type = PealType(type) if type else None
        self.date = date
        self.association = association
        self.tower = Tower.get(tower_id) if tower_id else None
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
        self.classification = classification
        self.is_spliced = is_spliced
        self.is_mixed = is_mixed
        self.is_variable_cover = is_variable_cover
        self.num_methods = num_methods
        self.num_principles = num_principles
        self.num_variants = num_variants
        self.method = Method.get(method_id) if method_id else None
        self.title = title
        self.duration = duration
        self.id = id

    @property
    def place(self) -> str:
        if self.tower:
            return self.tower.place
        else:
            return self.__place

    @place.setter
    def place(self, value: str):
        self.__place = value

    @property
    def sub_place(self) -> str:
        if self.tower:
            return self.tower.sub_place
        else:
            return self.__sub_place

    @sub_place.setter
    def sub_place(self, value: str):
        self.__sub_place = value

    @property
    def county(self) -> str:
        if self.tower:
            return self.tower.county
        else:
            return self.__county

    @county.setter
    def county(self, value: str):
        self.__county = value

    @property
    def country(self) -> str:
        if self.tower:
            return self.tower.country
        else:
            return self.__country

    @country.setter
    def country(self, value: str):
        self.__country = value

    @property
    def dedication(self) -> str:
        if self.tower:
            return self.tower.dedication
        else:
            return self.__dedication

    @dedication.setter
    def dedication(self, value: str):
        self.__dedication = value

    @property
    def tenor_weight(self) -> str:
        if self.tower:
            return self.tower.tenor_weight_in_cwt
        else:
            return self.__tenor_weight

    @tenor_weight.setter
    def tenor_weight(self, value: str):
        self.__tenor_weight = value

    @property
    def tenor_note(self) -> str:
        if self.tower:
            return self.tower.tenor_note
        else:
            return self.__tenor_note

    @tenor_note.setter
    def tenor_note(self, value: str):
        self.__tenor_note = value

    @property
    def tenor_description(self) -> str:
        text = self.tenor_weight
        if text and self.tenor_note:
            text += f' in {self.tenor_note}'
        return text

    @property
    def location(self) -> str:
        text = ''
        text += f'{self.place}' if self.place else ''
        text += f', {self.county}' if self.county else ''
        text += f', {self.country}' if self.country else ''
        text += '\n' if self.place or self.county or self.country else ''
        text += f'{self.address}' if self.address else ''
        text += f'{self.dedication}' if self.dedication else ''
        text += f', {self.sub_place}' if self.sub_place else ''
        if self.type == PealType.HANDBELLS:
            text += ' (in hand)'
        return text

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
    def num_methods_in_title(self):
        return (self.num_methods or 0) + (self.num_variants or 0) + (self.num_principles or 0)

    @property
    def is_multi_method(self):
        return self.is_mixed or self.is_spliced

    @property
    def method_title(self) -> str:
        if self.method and self.method.full_name:
            return self.method.full_name
        text = ''
        text += 'Spliced ' if self.is_spliced else ''
        text += 'Mixed ' if self.is_mixed else ''
        text += f'{self.title} ' if self.title else ''
        text += f'{self.classification} ' if self.classification else ''
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
        return text.strip()

    @property
    def ringers(self) -> list[tuple[Ringer, list[int], bool]]:
        if self.__ringers is None:
            self.__ringers = []
            self.__ringers_by_id = {}
            self.__ringers_by_bell = {}
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT r.id, pr.bell, pr.is_conductor FROM pealringers pr ' +
                    'JOIN ringers r ON pr.ringer_id = r.id ' +
                    'WHERE pr.peal_id = %s ' +
                    'ORDER BY pr.bell ASC',
                    (self.id,)).fetchall()
                last_ringer = None
                for ringer_id, bell, is_conductor in results:
                    if ringer_id == last_ringer:
                        self.__ringers[-1][1].append(bell)
                    else:
                        ringer = Ringer.get(ringer_id)
                        self.__ringers.append((ringer, [bell], is_conductor))
                        self.__ringers_by_bell[bell] = ringer
                        self.__ringers_by_id[ringer_id] = ringer
                    last_ringer = ringer_id
        return self.__ringers

    def add_ringer(self, ringer: Ringer, bells: list[int] = None, is_conductor: bool = False):
        self.ringers.append((ringer, bells, is_conductor))
        if ringer.id and ringer.id in self.__ringers_by_id:
            self.__ringers_by_id[ringer.id] = ringer
        if bells is not None:
            for bell in bells:
                self.__ringers_by_bell[bell] = ringer

    def clear_ringers(self):
        self.__ringers = None
        self.__ringers_by_id = None
        self.__ringers_by_bell = None

    @property
    def num_bells(self) -> int:
        return sum([len(ringer[1]) for ringer in self.ringers])

    @property
    def footnotes(self) -> list[tuple[str, int]]:
        if self.__footnotes is None:
            self.__footnotes = []
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT text, bell FROM pealfootnotes WHERE peal_id = %s', (self.id,)).fetchall()
                for footnote, bell in results:
                    self.__footnotes.append((footnote, bell))
        return self.__footnotes

    def add_footnote(self, bells: list[int], footnote: str):
        if bells is None:
            self.footnotes.append((footnote, None))
        else:
            for bell in bells:
                self.footnotes.append((footnote, bell))

    def commit(self):
        if self.id is None:
            result = Database.get_connection().query(
                f'INSERT INTO peals ({",".join(PEAL_FIELD_LIST)}) ' +
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (self.bellboard_id, self.type.value, self.date, self.association, self.tower.id if self.tower else None, self.__place,
                 self.__sub_place, self.address, self.dedication, self.__county, self.__country, self.__tenor_weight, self.__tenor_note,
                 self.changes, self.stage.value if self.stage else None, self.classification, self.is_spliced, self.is_mixed,
                 self.is_variable_cover, self.num_methods or 0, self.num_principles or 0, self.num_variants or 0,
                 self.method.id if self.method else None, self.title, self.duration))
            Database.get_connection().commit()
            self.id = result.lastrowid
            for method, changes in self.methods:
                Database.get_connection().query(
                    'INSERT INTO pealmethods (peal_id, method_id, changes) VALUES (%s, %s, %s)',
                    (self.id, method.id, changes))
            Database.get_connection().commit()
            for ringer, bells, is_conductor in self.ringers:
                if bells is None:
                    Database.get_connection().query(
                        'INSERT INTO pealringers (peal_id, ringer_id, is_conductor) VALUES (%s, %s, %s)',
                        (self.id, ringer.id, is_conductor))
                else:
                    for bell in bells:
                        Database.get_connection().query(
                            'INSERT INTO pealringers (peal_id, ringer_id, bell, is_conductor) VALUES (%s, %s, %s, %s)',
                            (self.id, ringer.id, bell, is_conductor))
            footnote_num = 1
            for footnote, bell in self.footnotes:
                Database.get_connection().query(
                    'INSERT INTO pealfootnotes (peal_id, footnote_num, bell, text) VALUES (%s, %s, %s, %s)',
                    (self.id, footnote_num, bell if bell else None, footnote))
                footnote_num += 1
            Database.get_connection().commit()
        else:
            raise NotImplementedError('Updating existing peals is not yet supported')

    def __str__(self):
        text = ''
        text += f'{self.association}\n' if self.association else ''
        text += self.location
        text += '\n'
        text += f'on {self.date.strftime("%A, %-d %B %Y")}\n' if self.date else ''
        text += f'{self.changes} ' if self.changes else ''
        text += self.method_title or f'"{self.title}"'
        text += ' '
        text += f'in {self.duration} mins ' if self.duration else ''
        text += f'({self.tenor_description})' if self.tenor_description else ''
        text += '\n'
        if len(self.methods) > 0:
            text += '('
            for method, changes in self.methods:
                text += f'{changes} ' if changes else ''
                text += f'{method.title}, '
            text = text.rstrip(', ')
            text += ')\n'
        text += '\n'
        for ringer in self.ringers:
            if ringer[1]:
                text += ','.join([str(bell) for bell in ringer[1]]) + ': '
            text += str(ringer[0])
            if ringer[2]:
                text += " (c)"
            text += '\n'
        text += '\n' if len(self.footnotes) else ''
        for footnote in self.footnotes:
            if footnote[1] and footnote[1] in self.__ringers_by_bell:
                text += f'[{footnote[1]}: {self.__ringers_by_bell[footnote[1]]}] '
            text += f'{footnote[0]}'
            text += '\n'
        text += '\n'
        text += f'[Imported Bellboard peal ID: {self.bellboard_id}]'
        return text

    @classmethod
    def get(self, id: int = None, bellboard_id: int = None) -> Peal:
        if id is None and bellboard_id is None:
            raise ValueError('Either peal database ID or Bellboard ID must be specified')
        result = Database.get_connection().query(
            f'SELECT {",".join(PEAL_FIELD_LIST)}, id ' +
            'FROM peals ' +
            'WHERE true ' +
            (f'AND id = {id} ' if id else '') +
            (f'AND bellboard_id = {bellboard_id} ' if bellboard_id else '')).fetchone()
        if result is None:
            return None
        return Peal(*result)

    @classmethod
    def get_all(self) -> dict[str, Peal]:
        return {result[0]: Peal(*result) for result in Database.get_connection().query(
            f'SELECT {",".join(PEAL_FIELD_LIST)}, id ' +
            'FROM peals').fetchall()
        }

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE pealfootnotes')
        Database.get_connection().query('TRUNCATE TABLE pealringers')
        Database.get_connection().query('TRUNCATE TABLE pealmethods')
        Database.get_connection().query('TRUNCATE TABLE peals')
        Database.get_connection().commit()
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
