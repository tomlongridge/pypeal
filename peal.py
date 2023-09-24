from __future__ import annotations
from datetime import datetime

from db import Database
from ringer import Ringer


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

    __ringers: list = None

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
    def ringers(self) -> list[tuple[Ringer, int, bool]]:
        if self.__ringers is None:
            results = Database.get_connection().query(
                'SELECT r.id, pr.bell, pr.is_conductor FROM pealringers pr ' +
                'JOIN ringers r ON pr.ringer_id = r.id ' +
                'WHERE pr.peal_id = %s ORDER BY pr.bell ASC',
                (self.id,)).fetchall()
            self.__ringers = [(Ringer.get(ringer_id), bell, is_conductor) for ringer_id, bell, is_conductor in results]
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

    def __str__(self):
        text = f'Peal {self.id} (Bellboard: https://bb.ringingworld.co.uk/view.php?id={self.bellboard_id}):\n'
        text += f'{self.association}\n' if self.association else ''
        text += f'{self.place}'
        text += f', {self.county}' if self.county else ''
        text += '\n'
        text += f'{self.address_dedication}\n' if self.address_dedication else ''
        text += f'on {self.date.strftime("%A, %-d %B %Y")}\n'
        text += f'in {self.duration} mins\n' if self.duration else ''
        if self.tenor_weight:
            text += f'({self.tenor_weight}'
            text += f' in {self.tenor_tone}' if self.tenor_tone else ''
            text += ')\n'
        for ringer in self.ringers:
            text += f'{ringer[1]} ' if ringer[1] else ''
            text += f'{ringer[0]}{" (c)" if ringer[2] else ""}\n'
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
    def get_all(self) -> list[Peal]:
        return [Peal(*result) for result in Database.get_connection().query(
            'SELECT ' +
            'bellboard_id, date, place, association, address_dedication, county, changes, title, duration, tenor_weight, tenor_tone, id ' +
            'FROM peals').fetchall()]

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
