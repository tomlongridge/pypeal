from datetime import datetime
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.prompt_add_association import prompt_add_association
from pypeal.cli.prompt_add_change_of_method import prompt_add_change_of_method
from pypeal.cli.prompt_add_composer import prompt_add_composer
from pypeal.cli.prompt_add_location import prompt_add_location
from pypeal.cli.prompt_add_ringer import prompt_add_ringer
from pypeal.cli.prompt_peal_title import prompt_peal_title
from pypeal.parsers import parse_duration, parse_footnote, parse_tenor_info
from pypeal.peal import PealType
from pypeal.tower import Tower


class PealPrompter(PealGeneratorListener):

    def type(self, value: PealType):
        self.peal.type = value

    def association(self, value: str):
        prompt_add_association(value, self.peal)

    def tower(self, dove_id: int = None, towerbase_id: int = None):
        if (tower := Tower.get(dove_id=dove_id, towerbase_id=towerbase_id)):
            self.peal.ring = tower.get_active_ring(self.peal.date)
            self.peal.place = None
            self.peal.county = None
            self.peal.address = None
            self.peal.dedication = None
        else:
            print(f'Tower ID {dove_id or towerbase_id} not recognised')

    def location(self, address_dedication: str, place: str, county: str):
        if self.peal.ring is None:
            prompt_add_location(address_dedication, place, county, self.peal)

    def changes(self, value: int):
        self.peal.changes = value

    def title(self, value: str):
        prompt_peal_title(value, self.peal)

    def method_details(self, value: str):
        if value or self.peal.is_multi_method:
            prompt_add_change_of_method(value, self.peal)

    def composer(self, name: str, url: str):
        return prompt_add_composer(name, url, self.peal)

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
