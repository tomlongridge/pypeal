from __future__ import annotations

from db import Database
from ringer import Ringer


class Peal:

    bellboard_id: int
    id: int = None
    __ringers: list = None

    def __init__(self, bellboard_id: int, id: int = None):
        self.bellboard_id = bellboard_id
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
        text = f'Peal {self.id}:'
        for ringer in self.ringers:
            text += f'\n{ringer[1]} {ringer[0]}{" (c)" if ringer[2] else ""}'
        return text

    @classmethod
    def get(self, id: int) -> Peal:
        result = Database.get_connection().query('SELECT bellboard_id, id FROM peals WHERE id = %s', (id,)).fetchone()
        if result is None:
            return None
        return Peal(*result)

    @classmethod
    def get_all(self) -> list[Peal]:
        return [Peal(*result) for result in Database.get_connection().query('SELECT bellboard_id, id FROM peals').fetchall()]

    @classmethod
    def add(self, peal: Peal) -> Peal:
        result = Database.get_connection().query('INSERT INTO peals (bellboard_id) VALUES (%s)', (peal.bellboard_id,))
        Database.get_connection().commit()
        return self.get(result.lastrowid)
