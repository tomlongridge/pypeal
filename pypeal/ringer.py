from __future__ import annotations
from dataclasses import dataclass

from pypeal.db import Database


@dataclass
class Ringer:

    last_name: str
    given_names: str
    id: int = None

    def __str__(self) -> str:
        return f'{self.given_names} {self.last_name}'

    @classmethod
    def get(self, id: int) -> Ringer:
        # Get ringers with no link ID (i.e. the actual ringer, not aliases)
        result = Database.get_connection().query(
            'SELECT last_name, given_names, id FROM ringers WHERE id = %s', (id,)).fetchone()
        return Ringer(*result) if result else None

    @classmethod
    def get_by_full_name(cls, name: str) -> list[Ringer]:
        results = Database.get_connection().query(
            'SELECT last_name, given_names, id FROM ringers pr ' +
            f'WHERE CONCAT_WS(" ", given_names, last_name) = "{name}"' +
            'OR id IN (SELECT link_id FROM ringers ipr ' +
            f'WHERE ipr.link_id = pr.link_id AND CONCAT_WS(" ", given_names, last_name) = "{name}")').fetchall()
        return [Ringer(*result) for result in results]

    @classmethod
    def get_by_name(cls, last_name: str, given_names: str) -> list[Ringer]:
        return cls.get_by_full_name(f'{given_names} {last_name}')

    @classmethod
    def get_all(cls) -> list[Ringer]:
        return [Ringer(*result) for result in Database.get_connection().query(
            'SELECT last_name, given_names, id FROM ringers').fetchall()]

    @classmethod
    def add(cls, last_name: str, given_names: str) -> Ringer:
        result = Database.get_connection().query('INSERT INTO ringers (last_name, given_names) VALUES (%s, %s)', (last_name, given_names))
        Database.get_connection().commit()
        return cls.get(result.lastrowid)
