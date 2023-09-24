from __future__ import annotations
from dataclasses import dataclass

from db import Database


@dataclass
class Ringer:

    name: str
    id: int = None

    @classmethod
    def get(self, id: int) -> Ringer:
        result = Database.get_connection().query('SELECT name, id FROM ringers WHERE id = %s', (id,)).fetchone()
        if result is None:
            return None
        return Ringer(*result)

    @classmethod
    def get_by_name(self, name: str) -> Ringer:
        result = Database.get_connection().query('SELECT name, id FROM ringers WHERE name = %s', (name,)).fetchone()
        if result is None:
            return None
        return Ringer(*result)

    @classmethod
    def get_all(self) -> list[Ringer]:
        return [Ringer(*result) for result in Database.get_connection().query('SELECT * FROM ringers').fetchall()]

    @classmethod
    def add(self, name: str) -> Ringer:
        result = Database.get_connection().query('INSERT INTO ringers (name) VALUES (%s)', (name,))
        Database.get_connection().commit()
        return self.get(result.lastrowid)
