import datetime

from pypeal.peal import Peal, BellType


class PealGeneratorListener():

    def __init__(self):
        self.peal = None

    def new_peal(self, id: int):
        self.peal = Peal(bellboard_id=id)

    def bell_type(self, value: BellType):
        pass

    def tower(self, dove_id: int = None, towerbase_id: int = None):
        pass

    def association(self, value: str):
        pass

    def location(self, address_dedication: str, place: str, county: str):
        pass

    def changes(self, value: int):
        pass

    def title(self, value: str):
        pass

    def method_details(self, value: str):
        pass

    def composer(self, name: str, url: str):
        pass

    def date(self, value: datetime.date):
        pass

    def tenor(self, value: str):
        pass

    def duration(self, value: str):
        pass

    def ringer(self, name: str, bell_nums: list[int], bells: list[int], is_conductor: bool):
        pass

    def footnote(self, value: str):
        pass

    def event(self, url: str):
        pass

    def photo(self, caption: str, credit: str, url: str):
        pass

    def bellboard_metadata(self, submitter: str, date: datetime.date):
        pass

    def external_reference(self, value: str):
        pass

    def end_peal(self):
        pass
