class Cache():

    __instance = None

    def __init__(self):
        self._data: dict[str, dict[any, any]] = {}

    def get(self, cache: str, key: str) -> any:
        if cache in self._data and key in self._data[cache]:
            return self._data[cache][key]
        return None

    def add_all(self, cache: str, entities: dict) -> list[any]:
        cached_items = []
        for key, entity in entities.items():
            cached_items.append(self.add(cache, key, entity))
        return cached_items

    def add(self, cache: str, key: str, entity: any) -> any:
        if entity is None or key is None or cache is None:
            raise ValueError('Invalid cache request')
        if cache not in self._data:
            self._data[cache] = {}
        if key not in self._data[cache]:
            if type(entity) is dict:
                for k, v in entity.items():
                    self._data[cache][k] = v
            else:
                self._data[cache][key] = entity
        return self._data[cache][key]

    def clear(self, cache: str):
        if cache in self._data:
            self._data[cache].clear()

    @staticmethod
    def get_cache():
        if Cache.__instance is None:
            Cache.__instance = Cache()
        return Cache.__instance
