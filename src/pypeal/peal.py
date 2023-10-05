from __future__ import annotations
from datetime import datetime
from pypeal.db import Database
from pypeal.ringer import Ringer


class Peal:

    bellboard_id: int
    date: datetime.date
    place: str
    association: str
    address_dedication: str
    county: str
    changes: int
    title: str
    duration: int
    tenor_weight: str
    tenor_tone: str
    location_dove_id: int
    id: int

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
        self.title = title
        self.duration = duration
        self.tenor_weight = tenor_weight
        self.tenor_tone = tenor_tone
        self.id = id

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
                'INSERT INTO peals (' +
                'bellboard_id, date, place, association, address_dedication, county, changes, title, duration, tenor_weight, tenor_tone) ' +
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (self.bellboard_id, self.date, self.place, self.association, self.address_dedication, self.county, self.changes, self.title,
                 self.duration, self.tenor_weight, self.tenor_tone))
            Database.get_connection().commit()
            self.id = result.lastrowid
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
        text += f'on {self.date.strftime("%A, %-d %B %Y")} '
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
            'SELECT ' +
            'bellboard_id, date, place, association, address_dedication, county, changes, title, duration, tenor_weight, tenor_tone, id ' +
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
            'SELECT ' +
            'bellboard_id, date, place, association, address_dedication, county, changes, title, duration, tenor_weight, tenor_tone, id ' +
            'FROM peals').fetchall()
        }
