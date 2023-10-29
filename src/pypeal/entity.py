from __future__ import annotations
from typing import ClassVar


class CacheableEntity():

    __cache: ClassVar[dict[int, CacheableEntity]] = {}

    @property
    def id(self) -> int:
        pass

    @classmethod
    def _cache_result(cls, result: tuple | CacheableEntity) -> CacheableEntity:
        if result is None:
            return None
        entity = cls(*result) if type(result) is tuple else result
        if entity.id not in cls.__cache:
            cls.__cache[entity.id] = entity
        return cls.__cache[entity.id]

    @classmethod
    def _from_cache(cls, id: int) -> CacheableEntity:
        if id is not None and id in cls.__cache:
            return cls.__cache[id]
        return None

    @classmethod
    def _cache_results(cls, results: list[tuple | CacheableEntity]) -> list[CacheableEntity]:
        return [cls._cache_result(result) for result in results]
