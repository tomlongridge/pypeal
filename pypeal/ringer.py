from __future__ import annotations
from dataclasses import dataclass

from pypeal.db import Database


@dataclass
class Ringer:

    last_name: str
    given_names: str
    id: int = None

    def add_alias(self, last_name: str, given_names: str):
        Database.get_connection().query(
            'INSERT INTO ringers (last_name, given_names, link_id) VALUES (%s, %s, %s)', (last_name, given_names, self.id))
        Database.get_connection().commit()

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
            'WHERE ipr.link_id = pr.link_id AND ' +
            f'CONCAT_WS(" ", ipr.given_names, ipr.last_name) = "{name}")').fetchall()
        return [Ringer(*result) for result in results]

    @classmethod
    def get_by_name(cls, last_name: str = None, given_names: str = None) -> list[Ringer]:
        results = Database.get_connection().query(
            'SELECT last_name, given_names, id FROM ringers pr ' +
            'WHERE ' +
            f'(pr.last_name LIKE "{last_name if last_name and len(last_name.strip()) else "%"}" ' +
            f'AND pr.given_names LIKE "{given_names if given_names and len(given_names.strip()) else "%"}") ' +
            'OR id IN (SELECT link_id FROM ringers ipr ' +
            'WHERE ipr.link_id = pr.link_id AND ' +
            f'(ipr.last_name LIKE "{last_name if last_name and len(last_name.strip()) else "%"}" ' +
            f'AND ipr.given_names LIKE "{given_names if given_names and len(given_names.strip()) else "%"}"))').fetchall()
        return [Ringer(*result) for result in results]

    @classmethod
    def get_all(cls) -> list[Ringer]:
        return [Ringer(*result) for result in Database.get_connection().query(
            'SELECT last_name, given_names, id FROM ringers').fetchall()]

    @classmethod
    def add(cls, last_name: str, given_names: str) -> Ringer:
        result = Database.get_connection().query(
            'INSERT INTO ringers (last_name, given_names) VALUES (%s, %s)', (last_name, given_names))
        Database.get_connection().commit()
        return cls.get(result.lastrowid)
