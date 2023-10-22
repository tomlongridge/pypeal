import datetime


class PealGeneratorListener():

    def bellboard_id(self, id: int):
        pass

    def association(self, value: str):
        pass

    def place(self, value: str):
        pass

    def county(self, value: str):
        pass

    def address_dedication(self, value: str):
        pass

    def changes(self, value: int):
        pass

    def title(self, value: str):
        pass

    def method_details(self, value: str):
        pass

    def date(self, value: datetime):
        pass

    def tenor(self, value: str):
        pass

    def duration(self, value: str):
        pass

    def ringer(self, name: str, bells: list[int], is_conductor: bool):
        pass

    def footnote(self, value: str):
        pass
