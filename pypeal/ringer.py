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
        result = Database.get_connection().query('SELECT last_name, given_names, id FROM ringers WHERE id = %s', (id,)).fetchone()
        return Ringer(*result) if result else None

    @classmethod
    def get_by_full_name(self, name: str) -> list[Ringer]:
        results = Database.get_connection().query(
            f'SELECT last_name, given_names, id FROM ringers WHERE CONCAT_WS(" ", given_names, last_name) = "{name}"').fetchall()
        return [Ringer(*result) for result in results]

    @classmethod
    def get_by_name(self, last_name: str, given_names: str) -> list[Ringer]:
        results = Database.get_connection().query(
            'SELECT last_name, given_names, id FROM ringers WHERE last_name = %s and given_names = %s',
            (last_name, given_names)).fetchall()
        return [Ringer(*result) for result in results]

    @classmethod
    def get_all(self) -> list[Ringer]:
        return [Ringer(*result) for result in Database.get_connection().query('SELECT * FROM ringers').fetchall()]

    @classmethod
    def add(self, last_name: str, given_names: str) -> Ringer:
        result = Database.get_connection().query('INSERT INTO ringers (last_name, given_names) VALUES (%s, %s)', (last_name, given_names))
        Database.get_connection().commit()
        return self.get(result.lastrowid)
