import datetime

from pypeal.entities.peal import Peal, BellType


class PealGeneratorListener():

    def __init__(self):
        self.peal = None

    def new_peal(self, bellboard_id: int):
        self.peal = Peal(bellboard_id=bellboard_id)

    def bell_type(self, value: BellType):
        pass

    def tower(self, dove_id: int = None, towerbase_id: int = None):
        pass

    def association(self, value: str):
        pass

    def location(self, address_dedication: str, place: str, county: str, country: str):
        pass

    def changes(self, value: int):
        pass

    def title(self, value: str):
        pass

    def method_details(self, value: str):
        pass

    def composition_details(self, name: str, url: str, note: str):
        pass

    def date(self, value: datetime.date):
        pass

    def tenor(self, value: str):
        pass

    def duration(self, value: str):
        pass

    def ringer(self, name: str, bell_nums_in_peal: list[int], bell_nums_in_ring: list[int], is_conductor: bool, total_bells: int):
        pass

    def footnote(self, value: str):
        pass

    def event(self, url: str):
        pass

    def photo(self, url: str, caption: str, credit: str):
        pass

    def bellboard_metadata(self, submitter: str, created_date: datetime.date, updated_date: datetime.date):
        pass

    def external_reference(self, value: str):
        pass

    def end_peal(self):
        pass
