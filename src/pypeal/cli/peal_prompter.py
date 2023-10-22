import datetime
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.prompt_add_change_of_method import prompt_add_change_of_method
from pypeal.cli.prompt_add_ringer import prompt_add_ringer
from pypeal.cli.prompt_peal_title import prompt_peal_title
from pypeal.parsers import parse_duration, parse_footnote, parse_method_title, parse_tenor_info
from pypeal.peal import Peal


class PealListener(PealGeneratorListener):

    def __init__(self, peal: Peal):
        if not peal:
            raise ValueError('Peal passed to listener cannot be None')
        self.__peal = peal

    def bellboard_id(self, id: int):
        self.__peal.bellboard_id = id

    def association(self, value: str):
        self.__peal.association = value

    def place(self, value: str):
        self.__peal.place = value

    def county(self, value: str):
        self.__peal.county = value

    def address_dedication(self, value: str):
        self.__peal.address_dedication = value

    def changes(self, value: int):
        self.__peal.changes = value

    def title(self, value: str):
        parse_method_title(value, self.__peal)
        prompt_peal_title(self.__peal)

    def method_details(self, value: str):
        if value or self.__peal.is_multi_method:
            prompt_add_change_of_method(value, self.__peal)

    def date(self, value: datetime):
        self.__peal.date = value

    def tenor(self, value: str):
        if value:
            self.__peal.tenor_weight, self.__peal.tenor_tone = parse_tenor_info(value)

    def duration(self, value: str):
        if value:
            self.__peal.duration = parse_duration(value)

    def ringer(self, name: str, bells: list[int], is_conductor: bool):
        prompt_add_ringer(name, bells, is_conductor, self.__peal)

    def footnote(self, value: str):
        if value:
            parse_footnote(value, self.__peal)
