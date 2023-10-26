from datetime import datetime
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.prompt_add_change_of_method import prompt_add_change_of_method
from pypeal.cli.prompt_add_ringer import prompt_add_ringer
from pypeal.cli.prompt_peal_title import prompt_peal_title
from pypeal.parsers import parse_duration, parse_footnote, parse_tenor_info
from pypeal.tower import Tower


class PealPrompter(PealGeneratorListener):

    def association(self, value: str):
        self.peal.association = value

    def tower(self, value: int):
        self.peal.tower = Tower.get(value)
        self.peal.place = None
        self.peal.county = None
        self.peal.address_dedication = None

    def place(self, value: str):
        if self.peal.tower is None:
            self.peal.place = value

    def county(self, value: str):
        if self.peal.tower is None:
            self.peal.county = value

    def address_dedication(self, value: str):
        if self.peal.tower is None:
            self.peal.address_dedication = value

    def changes(self, value: int):
        self.peal.changes = value

    def title(self, value: str):
        prompt_peal_title(value, self.peal)

    def method_details(self, value: str):
        if value or self.peal.is_multi_method:
            prompt_add_change_of_method(value, self.peal)

    def date(self, value: datetime):
        self.peal.date = value

    def tenor(self, value: str):
        if value:
            self.peal.tenor_weight, self.peal.tenor_note = parse_tenor_info(value)

    def duration(self, value: str):
        if value:
            self.peal.duration = parse_duration(value)

    def ringer(self, name: str, bells: list[int], is_conductor: bool):
        prompt_add_ringer(name, bells, is_conductor, self.peal)

    def footnote(self, value: str):
        if value:
            parse_footnote(value, self.peal)
