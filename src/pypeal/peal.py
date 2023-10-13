from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pypeal.db import Database
from pypeal.method import Method, Stage
from pypeal.ringer import Ringer

PEAL_FIELD_LIST: list[str] = ['bellboard_id', 'date', 'place', 'association', 'address_dedication', 'county', 'changes', 'stage',
                              'classification', 'is_spliced', 'is_mixed', 'is_variable_cover', 'num_methods', 'num_principles',
                              'num_variants', 'method_id', 'title', 'duration', 'tenor_weight', 'tenor_tone']


@dataclass
class Peal:

    bellboard_id: int
    date: datetime.date
    place: str
    association: str
    address_dedication: str
    county: str
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
    tenor_weight: str
    tenor_tone: str
    id: int

    __methods: list[tuple[Method, int]] = None

    __ringers: list[(Ringer, list[int], bool)] = None
    __ringers_by_id: dict[int, Ringer] = None
    __ringers_by_bell: dict[int, Ringer] = None

    __footnotes: list[(str, int)] = None

    def __init__(self,
                 bellboard_id: int,
                 date: datetime.date = None,
                 place: str = None,
                 association: str = None,
                 address_dedication: str = None,
                 county: str = None,
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
                 tenor_weight: str = None,
                 tenor_tone: str = None,
                 id: int = None):
        self.bellboard_id = bellboard_id
        self.date = date
        self.place = place
        self.association = association
        self.address_dedication = address_dedication
        self.county = county
        self.changes = changes
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
        self.tenor_weight = tenor_weight
        self.tenor_tone = tenor_tone
        self.id = id

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
        self.methods.append((method, changes))

    @property
    def method_title(self) -> str:
        if self.method:
            return self.method.full_name
        text = ''
        text += 'Spliced ' if self.is_spliced else ''
        text += 'Mixed ' if self.is_mixed else ''
        text += f'{self.title} ' if self.title else ''
        text += f'{self.classification} ' if self.classification else ''
        text += f'{self.stage.name.capitalize()} ' if self.stage else ''
        if self.num_methods + self.num_principles + self.num_variants > 0:
            text += '('
            text += f'{self.num_methods}m/' if self.num_methods else ''
            text += f'{self.num_principles}p/' if self.num_principles else ''
            text += f'{self.num_variants}v/' if self.num_variants else ''
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
    def footnotes(self) -> list[tuple[str, int]]:
        if self.__footnotes is None:
            self.__footnotes = []
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT text, bell FROM pealfootnotes WHERE peal_id = %s', (self.id,)).fetchall()
                for footnote, bell in results:
                    self.__footnotes.append((footnote, bell))
        return self.__footnotes

    def add_footnote(self, bell: int, footnote: str):
        self.footnotes.append((footnote, bell))

    def commit(self):
        if self.id is None:
            result = Database.get_connection().query(
                f'INSERT INTO peals ({",".join(PEAL_FIELD_LIST)}) ' +
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (self.bellboard_id, self.date, self.place, self.association, self.address_dedication, self.county, self.changes,
                 self.stage.value if self.stage else None, self.classification, self.is_spliced, self.is_mixed, self.is_variable_cover,
                 self.num_methods, self.num_principles, self.num_variants, self.method.id if self.method else None, self.title,
                 self.duration, self.tenor_weight, self.tenor_tone))
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
        text += f'{self.place}'
        text += f', {self.county}' if self.county else ''
        text += '\n'
        text += f'{self.address_dedication}\n' if self.address_dedication else ''
        text += f'on {self.date.strftime("%A, %-d %B %Y")}\n'
        text += f'{self.changes} ' if self.changes else ''
        text += self.method_title or f'"{self.title}"'
        text += ' '
        text += f'in {self.duration} mins ' if self.duration else ''
        if self.tenor_weight:
            text += f'({self.tenor_weight}'
            text += f' in {self.tenor_tone}' if self.tenor_tone else ''
            text += ')'
        text += '\n\n'
        for ringer in self.ringers:
            if ringer[1]:
                text += ','.join([str(bell) for bell in ringer[1]]) + ': '
            text += str(ringer[0])
            if ringer[2]:
                text += " (c)"
            text += '\n'
        text += '\n' if len(self.footnotes) else ''
        for footnote in self.footnotes:
            if footnote[1]:
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
