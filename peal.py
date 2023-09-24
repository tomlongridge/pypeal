from __future__ import annotations
from dataclasses import dataclass

from db import Database
from ringer import Ringer


@dataclass
class Peal:

    bellboard_id: int
    id: int = None

    def add_ringer(self, ringer: Ringer, bells: list[int] = None):
        if bells is None:
            Database.get_connection().query(
                'INSERT INTO pealringers (peal_id, ringer_id) VALUES (%s, %s)', (self.id, ringer.id))
        else:
            for bell in bells:
                Database.get_connection().query(
                    'INSERT INTO pealringers (peal_id, ringer_id, bell) VALUES (%s, %s, %s)', (self.id, ringer.id, bell))
        Database.get_connection().commit()

    def get_ringers(self) -> list[tuple[Ringer, int]]:
        results = Database.get_connection().query(
            'SELECT r.id, pr.bell FROM pealringers pr JOIN ringers r ON pr.ringer_id = r.id WHERE pr.peal_id = %s ORDER BY pr.bell ASC',
            (self.id,)).fetchall()
        return [(Ringer.get(ringer_id), bell) for ringer_id, bell in results]

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
