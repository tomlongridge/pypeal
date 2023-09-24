from __future__ import annotations
from dataclasses import dataclass

from db import Database


@dataclass
class Ringer:

    id: int
    name: str

    @classmethod
    def get_ringer(self, ringer_id: int) -> Ringer:
        result = Database.get_connection().query('SELECT id, name FROM ringers WHERE id = %s', (ringer_id,)).fetchone()
        if result is None:
            return None
        return Ringer(*result)

    @classmethod
    def get_ringer_by_name(self, name: str) -> Ringer:
        result = Database.get_connection().query('SELECT * FROM ringers WHERE name = %s', (name,)).fetchone()
        if result is None:
            return None
        return Ringer(*result)

    @classmethod
    def get_ringers(self) -> list[Ringer]:
        return [Ringer(*result) for result in Database.get_connection().query('SELECT * FROM ringers').fetchall()]

    @classmethod
    def add_ringer(self, name: str) -> Ringer:
        result = Database.get_connection().query('INSERT INTO ringers (name) VALUES (%s)', (name,))
        Database.get_connection().commit()
        return self.get_ringer(result.lastrowid)
