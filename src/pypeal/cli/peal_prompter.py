from datetime import datetime
from pypeal import utils
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.prompt_add_footnote import prompt_add_footnote, prompt_add_muffle_type
from pypeal.cli.prompt_validate_footnotes import prompt_validate_footnotes
from pypeal.cli.prompt_validate_tenor import prompt_validate_tenor
from pypeal.cli.prompt_add_association import prompt_add_association
from pypeal.cli.prompt_add_change_of_method import prompt_add_change_of_method
from pypeal.cli.prompt_add_composer import prompt_add_composer
from pypeal.cli.prompt_add_location import prompt_add_location
from pypeal.cli.prompt_add_ringer import prompt_add_ringer
from pypeal.cli.prompt_peal_title import prompt_peal_title
from pypeal.cli.prompts import UserCancelled, confirm, error
from pypeal.parsers import parse_duration, parse_tenor_info
from pypeal.peal import Peal, BellType, PealType
from pypeal.tower import Tower


class PealPromptListener(PealGeneratorListener):

    peal: Peal
    quick_mode: bool

    def __init__(self):
        self.peal = None
        self.quick_mode = False

    def new_peal(self, id: int):
        self.peal = Peal(bellboard_id=id)

    def bell_type(self, value: BellType):
        self.peal.bell_type = value
        print(f'🔔 Bell type: {value.name.capitalize()}')

    def association(self, value: str):
        self._run_cancellable_prompt(
            lambda peal: prompt_add_association(value, peal, self.quick_mode))
        print(f'🏛 Association: {value or "None"}')

    def tower(self, dove_id: int = None, towerbase_id: int = None):
        if (tower := Tower.get(dove_id=dove_id, towerbase_id=towerbase_id)):
            self.peal.ring = tower.get_active_ring(self.peal.date)
            self.peal.place = None
            self.peal.county = None
            self.peal.address = None
            self.peal.dedication = None
            print(f'🏰 Tower: {tower.name}')
        else:
            print(f'Tower ID {dove_id or towerbase_id} not found')

    def location(self, address_dedication: str, place: str, county: str):
        if self.peal.ring is None:
            self._run_cancellable_prompt(
                lambda peal: prompt_add_location(address_dedication, place, county, peal, self.quick_mode))
            if self.peal.location:
                print('📍 Location', self.peal.location)
            if self.peal.location_detail:
                print('📍 Detail', self.peal.location_detail)

    def changes(self, value: int):
        self.peal.changes = value
        print(f'🔢 Changes: {value or "Unknown"}')

    def title(self, value: str):
        self._run_cancellable_prompt(
            lambda peal: prompt_peal_title(value, peal, self.quick_mode))
        if self.peal.title:
            print(f'📕 Title: {self.peal.title}')

    def method_details(self, value: str):
        if self.peal.length_type is None:
            self.peal.detail = value
            if value:
                print(f'📝 Details: {value}')
        elif value or self.peal.type in [PealType.MIXED_METHODS, PealType.SPLICED_METHODS]:
            self._run_cancellable_prompt(
                lambda peal: prompt_add_change_of_method(value, peal, self.quick_mode))
            print('📝 Method details:')
            for method in self.peal.methods:
                print(f'  - {method[0].full_name}' + (f' ({method[1]})' if method[1] else ''))

    def composer(self, name: str, url: str):
        self._run_cancellable_prompt(
            lambda peal: prompt_add_composer(name, url, peal, self.quick_mode))
        print(f'🎼 Composer: {self.peal.composer or "Unknown"}')

    def date(self, value: datetime.date):
        self.peal.date = value
        print(f'📅 Date: {utils.format_date_full(value)}')

    def tenor(self, value: str):
        if value:
            self.peal.tenor_weight, self.peal.tenor_note = parse_tenor_info(value)
            print(f'🔔 Tenor: {self.peal.tenor_weight}' +
                  (f' in {self.peal.tenor_note}' if self.peal.tenor_note else ''))
        else:
            print('🔔 Tenor: Unknown')

    def duration(self, value: str):
        if value:
            self.peal.duration = parse_duration(value)
        print(f'⏱ Duration: {self.peal.duration or "Unknown"}')

    def ringer(self, name: str, bell_nums: list[int], bells: list[int], is_conductor: bool):
        self._run_cancellable_prompt(
            lambda peal: prompt_add_ringer(name, bell_nums, bells, is_conductor, peal, self.quick_mode))
        print(f'👤 Ringer: {self.peal.get_ringer_line(self.peal.ringers[-1])}')

    def footnote(self, value: str):
        if value:
            self._run_cancellable_prompt(
                lambda peal: prompt_add_footnote(value, peal, self.quick_mode))
            print(f'📝 Footnote: {self.peal.get_footnote_line(self.peal.footnotes[-1])}')

    def event(self, url: str):
        if url:
            self.peal.event_url = url
        print(f'🔗 Event link: {self.peal.event_url or "None"}')

    def end_peal(self):
        self._run_cancellable_prompt(lambda peal: prompt_validate_tenor(peal, self.quick_mode))
        self._run_cancellable_prompt(lambda peal: prompt_validate_footnotes(peal, self.quick_mode))

        if not self.quick_mode:
            self._run_cancellable_prompt(lambda peal: prompt_add_footnote(None, peal, False))
        if len(self.peal.footnotes) == 0:
            print('📝 Footnotes: None')

        if not self.quick_mode:
            self._run_cancellable_prompt(lambda peal: prompt_add_muffle_type(peal))
        print(f'🔕 Muffles: {self.peal.muffles.name.capitalize() if self.peal.muffles else "None"}')

    # Runs the prompt with a copy of the peal, so the original is not modified if the user cancels
    def _run_cancellable_prompt(self, prompt: callable):
        working_peal = self.peal.copy()
        while True:
            try:
                prompt(working_peal)
                break
            except UserCancelled as e:
                error('Cancelled input')
                if confirm(None, confirm_message='Retry?', default=True):
                    continue
                else:
                    raise e
        self.peal = working_peal
