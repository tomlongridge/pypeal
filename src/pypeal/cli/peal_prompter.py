from datetime import datetime
from pypeal import utils
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.prompt_add_bell_type import prompt_add_bell_type
from pypeal.cli.prompt_add_changes import prompt_add_changes
from pypeal.cli.prompt_add_duration import prompt_add_duration
from pypeal.cli.prompt_add_footnote import prompt_add_footnote, prompt_add_muffle_type
from pypeal.cli.prompt_add_tenor import prompt_add_tenor, prompt_validate_tenor
from pypeal.cli.prompt_add_association import prompt_add_association
from pypeal.cli.prompt_add_change_of_method import prompt_add_change_of_method_from_string
from pypeal.cli.prompt_add_composition_details import prompt_add_composition_details
from pypeal.cli.prompt_add_location import prompt_add_location
from pypeal.cli.prompt_add_ringer import prompt_add_ringer
from pypeal.cli.prompt_peal_title import prompt_peal_title
from pypeal.cli.prompts import UserCancelled, confirm, error
from pypeal.entities.peal import Peal, BellType, PealLengthType, PealType
from pypeal.entities.tower import Tower


class PealPromptListener(PealGeneratorListener):

    def __init__(self):
        super().__init__()
        self.quick_mode = False
        self.footnote_amend = True

    def set_quick_mode(self, quick_mode: bool = True, amend_footnote: bool = False):
        self.quick_mode = quick_mode
        self.footnote_amend = amend_footnote

    def new_peal(self, id: int):
        self.peal = Peal(bellboard_id=id)

    def bell_type(self, value: BellType):
        if value:
            self.peal.bell_type = value
            print(f'🔔 Bell type: {value.name.capitalize()}')

    def association(self, value: str):
        value = _clean_str_input(value)
        self._run_cancellable_prompt(
            lambda peal: prompt_add_association(value, peal, self.quick_mode))
        print(f'🏛 Association: {self.peal.association or "None"}')

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

    def location(self, address_dedication: str, place: str, county: str, country: str):
        address_dedication = _clean_str_input(address_dedication)
        place = _clean_str_input(place)
        county = _clean_str_input(county)
        if self.peal.ring is None:
            self._run_cancellable_prompt(
                lambda peal: prompt_add_location(address_dedication, place, county, country, peal, self.quick_mode))
            if self.peal.location:
                print(f'📍 Location: {self.peal.location}')
            if self.peal.location_detail:
                print(f'📍 Detail: {self.peal.location_detail}')

    def changes(self, value: str):
        value = _clean_str_input(value)
        self._run_cancellable_prompt(
            lambda peal: prompt_add_changes(value, peal, self.quick_mode))
        print(f'🔢 Changes: {self.peal.changes}')

    def title(self, value: str):
        value = _clean_str_input(value)
        if not value:
            raise ValueError('Peal title cannot be empty')
        self._run_cancellable_prompt(
            lambda peal: prompt_peal_title(value, peal, self.quick_mode))
        if self.peal.bellboard_id is not None:
            self.peal.published_title = value
        if self.peal.title:
            print(f'📕 Title: {self.peal.title}')

    def method_details(self, value: str):
        value = _clean_str_input(value)
        # A non-peal performance will have general text about the performance
        # e.g. "Rounds and call changes"
        if self.peal.length_type == PealLengthType.NONE:
            self.peal.detail = value
            if value:
                print(f'📝 Details: {value}')
            return

        # If we have method details then prompt for entry, but also if the peal is multi-method but we haven't got
        # any specific methods yet. If the title contained the methods, these will already have been added
        # e.g. "Spliced Cambridge and Yorkshire Royal"
        if value or self.peal.type in [PealType.MIXED_METHODS, PealType.SPLICED_METHODS]:
            if len(self.peal.methods) == 0:
                self._run_cancellable_prompt(
                    lambda peal: prompt_add_change_of_method_from_string(value, peal, self.quick_mode))
            print('📝 Method details:')
            if len(self.peal.methods) > 0:
                for method in self.peal.methods:
                    print(f'  - {method[0].full_name}' + (f' ({method[1]})' if method[1] else ''))
            else:
                print('  - None')

    def composition_details(self, name: str, url: str, note: str):
        name = _clean_str_input(name)
        url = _clean_str_input(url)
        self._run_cancellable_prompt(
            lambda peal: prompt_add_composition_details(name, url, note, peal, self.quick_mode))
        print(f'🎼 Composer: {self.peal.composer or "Unknown"}')
        if self.peal.composition_note:
            print(f'🎼 Composition: {self.peal.composition_note}')

    def date(self, value: datetime.date):
        self.peal.date = value
        print(f'📅 Date: {utils.format_date_full(value)}')

    def tenor(self, value: str):
        value = _clean_str_input(value)
        if value:
            self._run_cancellable_prompt(
                lambda peal: prompt_add_tenor(value, peal, self.quick_mode))
            print(f'🔔 Tenor: {self.peal.tenor_weight}' +
                  (f' in {self.peal.tenor_note}' if self.peal.tenor_note else ''))
        else:
            print('🔔 Tenor: Unknown')

    def duration(self, value: str):
        value = _clean_str_input(value)
        self._run_cancellable_prompt(
            lambda peal: prompt_add_duration(value, peal, self.quick_mode))
        print(f'⏱ Duration: {utils.get_time_str(self.peal.duration, full=True)}')

    def ringer(self, name: str, bell_nums_in_peal: list[int], bell_nums_in_ring: list[int], is_conductor: bool, total_bells: int):
        name = _clean_str_input(name)
        self._run_cancellable_prompt(
            lambda peal: prompt_add_ringer(name, bell_nums_in_peal, bell_nums_in_ring, is_conductor, total_bells, peal, self.quick_mode))
        print(f'👤 Ringer: {self.peal.get_ringer_line(self.peal.ringers[-1])}')

    def footnote(self, value: str):
        value = _clean_str_input(value)
        if value:
            self._run_cancellable_prompt(
                lambda peal: prompt_add_footnote(value, peal, self.quick_mode and not self.footnote_amend))
        else:
            if not self.quick_mode or self.footnote_amend:
                self._run_cancellable_prompt(lambda peal: prompt_add_footnote(None, peal, False))
            if len(self.peal.footnotes) == 0:
                print('📝 Footnotes: None')
            else:
                print('📝 Footnotes:')
                for footnote in self.peal.footnotes:
                    print(f'  - {footnote}')

    def event(self, url: str):
        url = _clean_str_input(url)
        if url:
            self.peal.event_url = url
        print(f'🔗 Event link: {self.peal.event_url or "None"}')

    def photo(self, url: str, caption: str, credit: str):
        url = _clean_str_input(url)
        caption = _clean_str_input(caption)
        credit = _clean_str_input(credit)
        if url:
            self.peal.add_photo(url, caption, credit)
        print(f'📷 Photo link: {url or "None"}')
        if caption:
            print(f'  - {caption}')
        if credit:
            print(f'  - Photo credit: {credit}')

    def bellboard_metadata(self, submitter: str, created_date: datetime.date, updated_date: datetime.date):
        submitter = _clean_str_input(submitter)
        self.peal.bellboard_submitter = submitter
        self.peal.bellboard_submitted_date = created_date
        print(f'📮 Submitted by: {self.peal.bellboard_submitter or "Unknown"} on ' +
              utils.format_date_full(self.peal.bellboard_submitted_date)
              if self.peal.bellboard_submitted_date else 'Unknown')
        if updated_date:
            print(f'✏️ Updated: {utils.format_date_full(updated_date)}')

    def external_reference(self, value: str):
        value = _clean_str_input(value)
        self.peal.external_reference = value
        print(f'🔗 External reference: {self.peal.external_reference or "None"}')

    def end_peal(self):

        self._run_cancellable_prompt(lambda peal: prompt_validate_tenor(peal, self.quick_mode))

        self._run_cancellable_prompt(lambda peal: prompt_add_bell_type(peal, self.quick_mode))
        print(f'🔔 Bell type: {self.peal.bell_type.name.capitalize()}')

        if not self.quick_mode:
            self._run_cancellable_prompt(lambda peal: prompt_add_muffle_type(peal))
        print(f'🔕 Muffles: {self.peal.muffles.name.capitalize() if self.peal.muffles else "None"}')

    # Runs the prompt with a copy of the peal, so the original is not modified if the user cancels
    def _run_cancellable_prompt(self, prompt: callable):
        restore_peal = self.peal.copy()
        while True:
            try:
                prompt(self.peal)
                break
            except UserCancelled as e:
                error('Cancelled input')
                if confirm(None, confirm_message='Retry current input?', default=True):
                    self.peal = restore_peal
                    continue
                else:
                    raise e


def _clean_str_input(input: str) -> str:
    input = utils.strip_internal_space(input)
    input = utils.strip_smart_quotes(input)
    if input and len(input.strip()) == 0:
        input = None
    return input
