from __future__ import annotations
from datetime import datetime
import re
from pypeal import bellboard

from pypeal.db import Database
from pypeal.ringer import Ringer

FOOTNOTE_RINGER_REGEX_PREFIX = re.compile(r'^(?P<bells>[0-9,\s]+)\s?[-:]\s(?P<footnote>.*)$')
FOOTNOTE_RINGER_REGEX_SUFFIX = re.compile(r'^(?P<footnote>.*)\s?[-:]\s(?P<bells>[0-9,\s]+)\.?$')


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

    __ringers: list[(Ringer, int, bool)] = None
    __ringers_by_id: dict[int, Ringer] = None
    __ringers_by_bell: dict[int, Ringer] = None

    __footnotes: list[(str, Ringer)] = None

    def __init__(self,
                 bellboard_id: int,
                 date: datetime.date,
                 place: str,
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
    def bellboard_url(self) -> str:
        return bellboard.get_url_from_id(self.bellboard_id)

    @property
    def ringers(self) -> list[tuple[Ringer, int, bool]]:
        if self.__ringers is None:
            results = Database.get_connection().query(
                'SELECT r.id, pr.bell, pr.is_conductor FROM pealringers pr ' +
                'JOIN ringers r ON pr.ringer_id = r.id ' +
                'WHERE pr.peal_id = %s ORDER BY pr.bell ASC',
                (self.id,)).fetchall()
            self.__ringers = []
            self.__ringers_by_id = {}
            for ringer_id, bell, is_conductor in results:
                self.__add_bell_ringer(ringer_id, [bell], is_conductor)
        return self.__ringers

    def add_ringer(self, ringer: Ringer, bells: list[int] = None, is_conductor: bool = False):
        if bells is None:
            Database.get_connection().query(
                'INSERT INTO pealringers (peal_id, ringer_id, is_conductor) VALUES (%s, %s, %s)',
                (self.id, ringer.id, is_conductor))
        else:
            for bell in bells:
                Database.get_connection().query(
                    'INSERT INTO pealringers (peal_id, ringer_id, bell, is_conductor) VALUES (%s, %s, %s, %s)',
                    (self.id, ringer.id, bell, is_conductor))
        Database.get_connection().commit()
        self.__add_bell_ringer(ringer.id, bells, is_conductor)

    def __add_bell_ringer(self, ringer_id: int, bells: list[int] = None, is_conductor: bool = False):
        if self.__ringers is None:
            self.__ringers = []
            self.__ringers_by_id = {}
            self.__ringers_by_bell = {}
        if ringer_id in self.__ringers_by_id:
            ringer = self.__ringers_by_id[ringer_id]
        else:
            ringer = Ringer.get(ringer_id)
            self.__ringers_by_id[ringer.id] = ringer
        if bells is None:
            self.__ringers.append((ringer, None, is_conductor))
        else:
            for bell in bells:
                self.__ringers.append((ringer, bell, is_conductor))
                self.__ringers_by_bell[bell] = ringer

    @property
    def footnotes(self) -> list[str]:
        if self.__footnotes is None:
            results = Database.get_connection().query(
                'SELECT text, ringer_id FROM pealfootnotes WHERE peal_id = %s', (self.id,)).fetchall()
            self.__footnotes = []
            for footnote, ringer_id in results:
                self.__footnotes.append((footnote, self.__ringers_by_id[ringer_id] if ringer_id else None))
        return self.__footnotes

    def add_footnote(self, footnote: str, ringer: Ringer = None):
        if (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_PREFIX, footnote)) or \
           (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_SUFFIX, footnote)):
            footnote_info = footnote_match.groupdict()
            footnote = footnote_info['footnote'].strip()
            bells = footnote_info['bells'].split(',')
        else:
            bells = [None]

        for bell in bells:
            ringer_id = self.__ringers_by_bell[int(bell)].id if bell is not None else None
            Database.get_connection().query(
                'INSERT INTO pealfootnotes (peal_id, footnote_num, ringer_id, text) VALUES (%s, %s, %s, %s)',
                (self.id, len(self.footnotes), ringer_id, footnote))
            Database.get_connection().commit()
            self.__footnotes.append(footnote)

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
        text += '\n'
        for ringer in self.ringers:
            text += f'{ringer[1]} ' if ringer[1] else ''
            text += f'{ringer[0]}{" (c)" if ringer[2] else ""}\n'
        text += '\n' if self.footnotes else ''
        for footnote in self.footnotes:
            text += f'{footnote}\n'
        text += '\n'
        text += f'[Imported Bellboard peal ID: {self.bellboard_id}]'
        return text

    @classmethod
    def get(self, id: int) -> Peal:
        result = Database.get_connection().query(
            'SELECT ' +
            'bellboard_id, date, place, association, address_dedication, county, changes, title, duration, tenor_weight, tenor_tone, id ' +
            'FROM peals WHERE id = %s', (id,)).fetchone()
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

    @classmethod
    def add(self, peal: Peal) -> Peal:
        result = Database.get_connection().query(
            'INSERT INTO peals (' +
            'bellboard_id, date, place, association, address_dedication, county, changes, title, duration, tenor_weight, tenor_tone) ' +
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (peal.bellboard_id, peal.date, peal.place, peal.association, peal.address_dedication, peal.county, peal.changes, peal.title,
             peal.duration, peal.tenor_weight, peal.tenor_tone))
        Database.get_connection().commit()
        return self.get(result.lastrowid)
