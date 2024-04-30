from __future__ import annotations
import copy
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from itertools import zip_longest
import json
from pypeal import config, utils
from pypeal.entities.association import Association
from pypeal.bellboard.utils import get_url_from_id
from pypeal.cache import Cache
from pypeal.db import Database
from pypeal.entities.method import Classification, Method, Stage
from pypeal.entities.ringer import Ringer
from pypeal.entities.tower import Bell, Ring
from pypeal.utils import format_date_full, get_bell_label

FIELD_LIST: list[str] = ['bellboard_id', 'type', 'bell_type', 'date', 'association_id', 'ring_id', 'place', 'sub_place', 'address',
                         'dedication', 'county', 'country', 'changes', 'stage', 'classification', 'is_variable_cover', 'num_methods',
                         'num_principles', 'num_variants', 'method_id', 'title', 'published_title', 'detail', 'composer_id',
                         'composition_note', 'composition_url', 'duration', 'tenor_weight', 'tenor_note', 'event_url', 'muffles',
                         'external_reference', 'bellboard_submitter', 'bellboard_submitted_date', 'created_date']


class PealType(IntEnum):
    SINGLE_METHOD = 1
    MIXED_METHODS = 2
    SPLICED_METHODS = 3
    GENERAL_RINGING = 0

    def __str__(self):
        return self.name.replace("_", " ").title()


class PealLengthType(IntEnum):
    TOUCH = 1
    QUARTER_PEAL = 2
    HALF_PEAL = 3
    PEAL = 4
    LONG_LENGTH = 5
    NONE = 0

    def __str__(self):
        if self == PealLengthType.NONE:
            return 'General Ringing'
        else:
            return self.name.replace("_", " ").title()


class BellType(IntEnum):
    TOWER = 1
    HANDBELLS = 2

    def __str__(self):
        return self.name.replace("_", " ").title()


class MuffleType(IntEnum):
    HALF = 1
    FULLY = 2

    def __str__(self):
        return self.name.replace("_", " ").title() + ' muffled'


class PealRinger:
    def __init__(self, ringer: Ringer, bells: list[int], nums: list[int], is_conductor: bool = False, note: str = None):
        self.ringer: Ringer = ringer
        self.bell_ids: list[int] = bells
        self.bell_nums: list[int] = nums
        self.is_conductor: bool = is_conductor
        self.note: str = note


class Footnote:

    def __init__(self, text: str, bell: int, ringer: Ringer):
        self.text = text
        self.bell = bell
        self.ringer = ringer

    def __str__(self):
        value = ''
        if self.bell:
            value += f'[{self.bell}: {self.ringer}] '
        value += f'{self.text}'
        return value

    def __eq__(self, other: Footnote):
        return self.text == other.text and \
               self.bell == other.bell and \
               self.ringer == other.ringer


@dataclass
class Peal:

    bellboard_id: int
    type: PealType
    bell_type: BellType
    date: datetime.date
    association: Association
    ring: Ring
    address: str
    changes: int
    stage: Stage
    classification: Classification
    is_variable_cover: bool
    num_methods: int
    num_principles: int
    num_variants: int
    method: Method
    published_title: str
    detail: str
    composer: Ringer
    composition_note: str
    composition_url: str
    duration: int
    event_url: str
    muffles: MuffleType
    external_reference: str
    bellboard_submitter: str
    bellboard_submitted_date: datetime.date
    created_date: datetime
    id: int

    __title: str

    # Fields shared with Tower
    __place: str
    __sub_place: str
    __county: str
    __country: str
    __dedication: str
    __tenor_weight: int
    __tenor_note: str

    __methods: list[tuple[Method, int]]

    __ringers: list[PealRinger]
    __ringers_by_id: dict[int, Ringer]
    __ringers_by_num: dict[int, Ringer]

    __footnotes: list[Footnote]

    __photos: list[(int, str, str, str)]

    def __init__(self,
                 bellboard_id: int = None,
                 type: int = None,
                 bell_type: int = None,
                 date: datetime.date = None,
                 association_id: int = None,
                 ring_id: int = None,
                 place: str = None,
                 sub_place: str = None,
                 address: str = None,
                 dedication: str = None,
                 county: str = None,
                 country: str = None,
                 changes: int = None,
                 stage: int = None,
                 classification: str = None,
                 is_variable_cover: bool = False,
                 num_methods: int = None,
                 num_principles: int = None,
                 num_variants: int = None,
                 method_id: int = None,
                 title: str = None,
                 published_title: str = None,
                 detail: str = None,
                 composer_id: int = None,
                 composition_note: str = None,
                 composition_url: str = None,
                 duration: int = None,
                 tenor_weight: int = None,
                 tenor_note: str = None,
                 event_url: str = None,
                 muffles: int = None,
                 external_reference: str = None,
                 bellboard_submitter: str = None,
                 bellboard_submitted_date: datetime.date = None,
                 created_date: datetime = None,
                 id: int = None):
        self.bellboard_id = bellboard_id
        self.bell_type = BellType(bell_type) if bell_type else None
        self.type = PealType(type) if type is not None else None
        self.date = date
        self.association = Association.get(association_id) if association_id else None
        self.ring = Ring.get(ring_id) if ring_id else None
        self.__place = place
        self.__sub_place = sub_place
        self.address = address
        self.__dedication = dedication
        self.__county = county
        self.__country = country
        self.changes = changes
        self.__tenor_weight = tenor_weight
        self.__tenor_note = tenor_note
        self.stage = Stage(stage) if stage else None
        self.classification = Classification(classification) if classification else None
        self.is_variable_cover = is_variable_cover
        self.num_methods = num_methods
        self.num_principles = num_principles
        self.num_variants = num_variants
        self.method = Method.get(method_id) if method_id else None
        self.__title = title
        self.published_title = published_title
        self.detail = detail
        self.composer = Ringer.get(composer_id) if composer_id else None
        self.composition_note = composition_note
        self.composition_url = composition_url
        self.duration = duration
        self.event_url = event_url
        self.muffles = MuffleType(muffles) if muffles else None
        self.external_reference = external_reference
        self.bellboard_submitter = bellboard_submitter
        self.bellboard_submitted_date = bellboard_submitted_date
        self.created_date = created_date
        self.id = id

        self.__methods = None

        self.__ringers = None
        self.__ringers_by_id = None
        self.__ringers_by_num = None

        self.__footnotes = None
        self.__photos = None

    @property
    def place(self) -> str:
        if self.__place:
            return self.__place
        elif self.ring:
            return self.ring.tower.place
        else:
            return None

    @place.setter
    def place(self, value: str):
        self.__place = value

    @property
    def sub_place(self) -> str:
        if self.__sub_place:
            return self.__sub_place
        elif self.ring:
            return self.ring.tower.sub_place
        else:
            return None

    @sub_place.setter
    def sub_place(self, value: str):
        self.__sub_place = value

    @property
    def county(self) -> str:
        if self.__county:
            return self.__county
        elif self.ring:
            return self.ring.tower.county
        else:
            return None

    @county.setter
    def county(self, value: str):
        self.__county = value

    @property
    def country(self) -> str:
        if self.__country:
            return self.__country
        elif self.ring:
            return self.ring.tower.country
        else:
            return None

    @country.setter
    def country(self, value: str):
        self.__country = value

    @property
    def dedication(self) -> str:
        if self.__dedication:
            return self.__dedication
        elif self.ring:
            return self.ring.tower.dedication
        else:
            return None

    @dedication.setter
    def dedication(self, value: str):
        self.__dedication = value

    @property
    def tenor(self) -> Bell:
        if self.ring and len(self.ringers) > 0 and self.ringers[-1].bell_ids:
            return self.ring.get_bell_by_id(self.ringers[-1].bell_ids[-1])
        return None

    @property
    def tenor_weight(self) -> int:
        if self.__tenor_weight:
            return self.__tenor_weight
        elif self.tenor:
            return self.tenor.weight
        else:
            return None

    @tenor_weight.setter
    def tenor_weight(self, value: int):
        self.__tenor_weight = value

    @property
    def tenor_note(self) -> str:
        if self.__tenor_note:
            return self.__tenor_note
        if self.ring and self.tenor:
            return self.tenor.note
        else:
            return None

    @tenor_note.setter
    def tenor_note(self, value: str):
        self.__tenor_note = value

    @property
    def tenor_description(self) -> str:
        if self.tenor_weight:
            text = utils.get_weight_str(self.tenor_weight)
            if self.tenor_note:
                text += f' in {self.tenor_note}'
            return text
        return None

    @property
    def location_full(self) -> str:
        text = ''
        text += f'{self.place}' if self.place else ''
        text += f', {self.sub_place}' if self.sub_place else ''
        text += f' ({self.address})' if self.address else ''
        text += f' ({self.dedication})' if self.dedication else ''
        text += f', {self.county}' if self.county else ''
        text += f', {self.country}' if self.country else ''
        return text if len(text) > 0 else None

    @property
    def location(self) -> str:
        text = ''
        text += f'{self.place}' if self.place else ''
        text += f', {self.county}' if self.county else ''
        text += f', {self.country}' if self.country else ''
        return text if len(text) > 0 else None

    @property
    def location_detail(self) -> str:
        text = ''
        text += f'{self.address}' if self.address else ''
        text += f'{self.dedication}' if self.dedication else ''
        text += f', {self.sub_place}' if self.sub_place else ''
        return text if len(text) > 0 else None

    @property
    def methods(self) -> list[tuple[Method, int]]:
        if self.__methods is None:
            self.__methods = []
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT method_id, changes FROM pealmethods WHERE peal_id = %s', (self.id,)).fetchall()
                for method_id, changes in results:
                    self.__methods.append((Method.get(method_id), changes))
        return self.__methods

    def add_method(self, method: Method, changes: int = None):
        if method is not None:
            self.methods.append((method, changes))

    def clear_methods(self):
        self.__methods = None

    @property
    def num_methods_in_title(self) -> int:
        return (self.num_methods or 0) + (self.num_variants or 0) + (self.num_principles or 0)

    @property
    def length_type(self) -> PealLengthType:
        if self.changes is None:
            return PealLengthType.NONE
        if config.get_config('general', 'short_peal_threshold') is None \
                or self.stage is None \
                or self.stage.value >= config.get_config('general', 'short_peal_threshold'):
            if self.changes < 1250:
                return PealLengthType.TOUCH
            elif self.changes < 5000:
                return PealLengthType.QUARTER_PEAL
        else:
            if self.changes < 1260:
                return PealLengthType.TOUCH
            elif self.changes < 5040:
                return PealLengthType.QUARTER_PEAL
        if self.changes < 10_000:
            return PealLengthType.PEAL
        else:
            return PealLengthType.LONG_LENGTH

    @property
    def title(self) -> str:
        if self.method:
            return self.method.full_name
        text = ''
        text += 'Spliced ' if self.type == PealType.SPLICED_METHODS else ''
        text += 'Mixed ' if self.type == PealType.MIXED_METHODS else ''
        text += f'{self.classification.value} ' if self.classification else ''
        if self.stage and self.is_variable_cover and self.stage.value % 2 == 0:
            text += f'{Stage(self.stage.value - 1).name.capitalize()} and '
        text += f'{self.stage.name.capitalize()} ' if self.stage else ''
        if self.stage and self.is_variable_cover and self.stage.value % 2 == 1:
            text += f'and {Stage(self.stage.value + 1).name.capitalize()} '
        if self.num_methods_in_title > 0:
            text += '('
            text += f'{self.num_methods}m/' if self.num_methods else ''
            text += f'{self.num_variants}v/' if self.num_variants else ''
            text += f'{self.num_principles}p/' if self.num_principles else ''
            text = text.rstrip('/')
            text += ')'
        text = text.strip()
        if len(text) > 0:
            return text
        elif self.__title:
            return self.__title
        else:
            return 'Unknown'

    @title.setter
    def title(self, value: str):
        self.__title = value

    @property
    def ringers(self) -> list[PealRinger]:
        if self.__ringers is None:
            self.__ringers = []
            self.__ringers_by_id = {}
            self.__ringers_by_num = {}
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT r.id, pr.bell_id, pr.bell_num, pr.is_conductor, pr.note ' +
                    'FROM pealringers pr ' +
                    'JOIN ringers r ON pr.ringer_id = r.id ' +
                    'WHERE pr.peal_id = %s ' +
                    'ORDER BY pr.bell_num ASC',
                    (self.id,)).fetchall()
                last_ringer = None
                for ringer_id, bell_id, bell_num, is_conductor, note in results:
                    if ringer_id == last_ringer:
                        self.__ringers[-1].bell_nums.append(bell_num)
                        if bell_id:
                            self.__ringers[-1].bell_ids.append(bell_id)
                    else:
                        ringer = Ringer.get(ringer_id)
                        if bell_num == 0:
                            self.__ringers.append(PealRinger(ringer, None, None, is_conductor, note))
                        else:
                            self.__ringers.append(PealRinger(ringer, None, [bell_num], is_conductor, note))
                            if bell_id:
                                self.__ringers[-1].bell_ids = [bell_id]
                            self.__ringers_by_num[bell_num] = ringer
                            self.__ringers_by_id[ringer_id] = ringer
                    last_ringer = ringer_id
        return self.__ringers

    def get_ringer(self, num: int) -> Ringer:
        if num in self.__ringers_by_num:
            return self.__ringers_by_num[num]
        else:
            return None

    def get_ringer_line(self, peal_ringer: PealRinger) -> str:
        text = ''
        if peal_ringer.bell_nums:
            text += get_bell_label(peal_ringer.bell_nums)
            if peal_ringer.bell_ids:  # This is only applicable for tower bell peals
                bell_nums_in_tower = [self.ring.get_bell_by_id(bell_id).role for bell_id in peal_ringer.bell_ids]
                if bell_nums_in_tower != peal_ringer.bell_nums:
                    text += f' [{get_bell_label(bell_nums_in_tower)}]'
            text += ': '
        text += peal_ringer.ringer.get_name(self.date)
        if peal_ringer.note:
            text += f' ({peal_ringer.note})'
        if peal_ringer.is_conductor:
            text += " (c)"
        return text

    def add_ringer(self,
                   ringer: Ringer,
                   bell_ids: list[int] = None,
                   bell_nums: list[int] = None,
                   is_conductor: bool = False,
                   note: str = None):
        self.ringers.append(PealRinger(ringer, bell_ids, bell_nums, is_conductor, note))
        if ringer.id and ringer.id in self.__ringers_by_id:
            self.__ringers_by_id[ringer.id] = ringer
        for bell in bell_nums or []:
            self.__ringers_by_num[bell] = ringer

    def clear_ringers(self):
        self.__ringers = None
        self.__ringers_by_id = None
        self.__ringers_by_num = None

    @property
    def conductors(self) -> list[PealRinger]:
        conductor_list = []
        for ringer in self.ringers:
            if ringer.is_conductor:
                conductor_list.append(ringer)
        return conductor_list

    @property
    def num_bells(self) -> int:
        return sum([len(ringer.bell_nums) if ringer.bell_nums else 0 for ringer in self.ringers])

    @property
    def footnotes(self) -> list[Footnote]:
        if self.__footnotes is None:
            self.__footnotes = []
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT text, bell, ringer_id FROM pealfootnotes WHERE peal_id = %s', (self.id,)).fetchall()
                for footnote, bell, ringer_id in results:
                    self.__footnotes.append(Footnote(footnote, bell, Ringer.get(ringer_id) if ringer_id else None))
        return self.__footnotes

    def add_footnote(self, footnote: str, bell: int, ringer: Ringer):
        self.footnotes.append(Footnote(footnote, bell, ringer))

    @property
    def photos(self) -> list[tuple[int, str, str, str]]:
        if self.__photos is None:
            self.__photos = []
            if self.id is not None:
                results = Database.get_connection().query(
                    'SELECT url, caption, credit, id FROM pealphotos WHERE peal_id = %s', (self.id,)).fetchall()
                for url, caption, credit, photo_id in results:
                    self.__photos.append((photo_id, url, caption, credit))
        return self.__photos

    def add_photo(self, url: str, caption: str, credit: str):
        self.photos.append((None, url, caption, credit))

    def get_photo_bytes(self, photo_id: int) -> bytes:
        if self.id is None:
            raise ValueError('Peal must be committed to database before photos can be retrieved')
        result = Database.get_connection().query('SELECT photo FROM pealphotos WHERE id = %s', (photo_id,)).fetchone()
        return result[0] if result else None

    def set_photo_bytes(self, photo_id: int, photo: bytes):
        if self.id is None:
            raise ValueError('Peal must be committed to database before photo data can be added')
        Database.get_connection().query(
            'UPDATE pealphotos SET photo = %s WHERE id = %s', (photo, photo_id))
        Database.get_connection().commit()

    def commit(self):
        if self.id is not None:
            raise NotImplementedError('Updating existing peals is not yet supported')

        if self.type is None:
            raise ValueError('Peal type must be specified before it is saved')
        if not self.ringers:
            raise ValueError('Peal must have at least one ringer before it is saved')

        if self.ring and self.ring.id is None:
            self.ring.commit()

        self.created_date = utils.get_now()

        result = Database.get_connection().query(
            f'INSERT INTO peals ({",".join(FIELD_LIST)}) ' +
            f'VALUES ({("%s,"*len(FIELD_LIST)).strip(",")})',
            (self.bellboard_id, self.type.value, self.bell_type.value, self.date, self.association.id if self.association else None,
                self.ring.id if self.ring else None, self.__place, self.__sub_place, self.address, self.__dedication, self.__county,
                self.__country, self.changes, self.stage.value if self.stage else None,
                self.classification.value if self.classification else None, self.is_variable_cover, self.num_methods, self.num_principles,
                self.num_variants, self.method.id if self.method else None, self.title, self.published_title, self.detail,
                self.composer.id if self.composer else None, self.composition_note, self.composition_url, self.duration,
                self.__tenor_weight, self.__tenor_note, self.event_url, self.muffles.value if self.muffles else None,
                self.external_reference, self.bellboard_submitter, self.bellboard_submitted_date, self.created_date))
        Database.get_connection().commit()
        self.id = result.lastrowid
        for method, changes in self.methods:
            Database.get_connection().query(
                'INSERT INTO pealmethods (peal_id, method_id, changes) VALUES (%s, %s, %s)',
                (self.id, method.id, changes))
        Database.get_connection().commit()
        for peal_ringer in self.ringers:
            if peal_ringer.bell_nums is None:
                Database.get_connection().query(
                    'INSERT INTO pealringers (peal_id, ringer_id, is_conductor, note) VALUES (%s, %s, %s, %s)',
                    (self.id, peal_ringer.ringer.id, peal_ringer.is_conductor, peal_ringer.note))
            else:
                for bell_id, bell_num in zip_longest(peal_ringer.bell_ids or [], peal_ringer.bell_nums):
                    Database.get_connection().query(
                        'INSERT INTO pealringers (peal_id, ringer_id, bell_id, bell_num, is_conductor, note) ' +
                        'VALUES (%s, %s, %s, %s, %s, %s)',
                        (self.id, peal_ringer.ringer.id, bell_id, bell_num, peal_ringer.is_conductor or 0, peal_ringer.note))
        footnote_num = 1
        for footnote in self.footnotes:
            Database.get_connection().query(
                'INSERT INTO pealfootnotes (peal_id, footnote_num, bell, ringer_id, text) VALUES (%s, %s, %s, %s, %s)',
                (self.id, footnote_num, footnote.bell, footnote.ringer.id if footnote.ringer else None, footnote.text))
            footnote_num += 1
        Database.get_connection().commit()

        for i, photo in enumerate(self.photos):
            _, url, caption, credit = photo
            result = Database.get_connection().query(
                'INSERT INTO pealphotos (peal_id, url, caption, credit) VALUES (%s, %s, %s, %s)',
                (self.id, url, caption, credit))
            Database.get_connection().commit()
            self.__photos[i] = (result.lastrowid, url, caption, credit)

    def update_bellboard_id(self, bellboard_id: int, submitter: str = None, submitted_date: datetime = None):
        query = 'UPDATE peals SET bellboard_id = %(bellboard_id)s'
        params = {'bellboard_id': bellboard_id}
        if submitter:
            query += ', bellboard_submitter = %(submitter)s'
            params['submitter'] = submitter
        if submitted_date:
            query += ', bellboard_submitted_date = %(submitted_date)s'
            params['submitted_date'] = submitted_date
        query += ' WHERE id = %(id)s'
        params['id'] = self.id
        Database.get_connection().query(query, params)
        Database.get_connection().commit()
        self.bellboard_id = bellboard_id
        self.bellboard_submitter = submitter
        self.bellboard_submitted_date = submitted_date

    def delete(self):
        if self.id is None:
            raise ValueError('Peal must be committed to database before it can be deleted')
        Database.get_connection().query('DELETE FROM pealphotos WHERE peal_id = %s', (self.id,))
        Database.get_connection().query('DELETE FROM pealfootnotes WHERE peal_id = %s', (self.id,))
        Database.get_connection().query('DELETE FROM pealmethods WHERE peal_id = %s', (self.id,))
        Database.get_connection().query('DELETE FROM pealringers WHERE peal_id = %s', (self.id,))
        Database.get_connection().query('DELETE FROM peals WHERE id = %s', (self.id,))
        Database.get_connection().commit()
        Cache.get_cache().clear(Peal.__name__, f'D{self.id}')
        Cache.get_cache().clear(Peal.__name__, f'B{self.bellboard_id}')

    def get_method_summary(self) -> str:
        summary = ''
        if len(self.methods) == 0:
            return summary
        common_stage: Stage = self.methods[0][0].stage
        common_classification: Classification = self.methods[0][0].classification
        for method, _ in self.methods:
            if common_stage is not None and common_stage != method.stage:
                common_stage = None
            if common_classification is not None and common_classification != method.classification:
                common_classification = None

        sorted_methods = sorted(self.methods, key=lambda x: (-x[1] if x[1] else 0, x[0].full_name))

        previous_changes = None
        method: Method
        for method, changes in sorted_methods:
            if changes is not None and changes != previous_changes:
                summary += f'{changes} '
            method_name = method.full_name
            if common_stage:
                method_name = method_name.replace(f' {method.stage}', '')
            if common_classification:
                method_name = method_name.replace(f' {method.classification}', '')
            summary += f'{method_name}, '
            previous_changes = changes

        summary = summary.rstrip(', ')
        if ',' in summary:
            summary = summary.rsplit(',', 1)[0] + ' and' + summary.rsplit(',', 1)[1]
        return summary

    def get_footnote_summary(self) -> str:
        footnote_map: dict[str, list[int]] = {}
        for footnote in self.footnotes:
            if footnote.text not in footnote_map:
                footnote_map[footnote.text] = []
            if footnote.bell:
                footnote_map[footnote.text].append(footnote.bell)
                footnote_map[footnote.text].sort()
        summary = ''
        for text, bells in sorted(footnote_map.items(), key=lambda item: item[1][0] if len(item[1]) > 0 else 0):
            if bells and len(bells) < self.num_bells:
                summary += f'{utils.get_bell_label(bells)}: '
            summary += f'{text}\n'
        return summary.strip()

    def __str__(self):
        text = ''
        text += f'{self.association.name}\n' if self.association else ''
        text += f'{self.location}\n' if self.location else ''
        if self.location_detail:
            text += f'{self.location_detail}'
            if self.bell_type == BellType.HANDBELLS:
                text += ' (in hand)'
            text += '\n'
        text += f'On {format_date_full(self.date)}\n' if self.date else ''
        text += f'A {self.length_type.name.replace("_", " ").title()} of ' if self.length_type else ''
        text += f'{self.changes} ' if self.changes else ''
        text += self.title
        text += ' (half-muffled)' if self.muffles == MuffleType.HALF else ''
        text += ' (muffled)' if self.muffles == MuffleType.FULLY else ''
        text += ' '
        text += f'in {utils.get_time_str(self.duration, full=True)} ' if self.duration else ''
        text += f'({self.tenor_description})' if self.tenor_description else ''
        text += '\n'
        if len(self.methods) > 0:
            text += '('
            for method, changes in self.methods:
                text += f'{changes} ' if changes else ''
                text += f'{method.full_name}, '
            text = text.rstrip(', ')
            text += ')\n'
        text += f'{self.detail}\n' if self.detail else ''
        if self.composer:
            text += f'Composed by: {self.composer}\n'
        if self.composition_note:
            text += f'Composition: {self.composition_note}\n'
        text += '\n'
        for ringer in self.ringers:
            text += f'{self.get_ringer_line(ringer)}\n'
        if len(self.footnotes):
            text += '\n'
            text += self.get_footnote_summary()
            text += '\n'
        if self.bellboard_id:
            text += f'\n[BellBoard: {get_url_from_id(self.bellboard_id)}' if self.bellboard_id else ''
            text += ' (' if self.bellboard_submitter or self.bellboard_submitted_date else ''
            text += f'{self.bellboard_submitter}, ' if self.bellboard_submitter else ''
            text += f'{format_date_full(self.bellboard_submitted_date)})' if self.bellboard_submitted_date else ''
            text += ']'
        text += f'\n[Composition URL: {self.composition_url}]' if self.composition_url else ''
        text += f'\n[Event URL: {self.event_url}]' if self.event_url else ''
        text += f'\n[Published title: {self.published_title}]' if self.published_title is not None and \
            self.published_title != self.title else ''
        text += f'\n[External reference: {self.external_reference}]' if self.external_reference else ''
        text += f'\n[Database ID: {self.id}]' if self.id else ''
        return text.strip()

    def to_json(self):
        json_fields = {}
        return json.dumps(json_fields)

    def copy(self):
        return copy.deepcopy(self)

    def diff(self, other: Peal) -> dict[str, tuple[str, str]]:
        diffs = {}
        if self.bellboard_id != other.bellboard_id:
            diffs['bellboard_id'] = (str(self.bellboard_id), str(other.bellboard_id))
        if self.type != other.type:
            diffs['type'] = (str(self.type), str(other.type))
        if self.bell_type != other.bell_type:
            diffs['bell_type'] = (str(self.bell_type), str(other.bell_type))
        if self.date != other.date:
            diffs['date'] = (str(self.date), str(other.date))
        if self.association != other.association:
            diffs['association'] = (str(self.association), str(other.association))
        if self.ring != other.ring:
            diffs['ring'] = (str(self.ring), str(other.ring))
        if self.__place != other.__place:
            diffs['place'] = (str(self.__place), str(other.__place))
        if self.sub_place != other.sub_place:
            diffs['sub_place'] = (str(self.sub_place), str(other.sub_place))
        if self.address != other.address:
            diffs['address'] = (str(self.address), str(other.address))
        if self.dedication != other.dedication:
            diffs['dedication'] = (str(self.dedication), str(other.dedication))
        if self.county != other.county:
            diffs['county'] = (str(self.county), str(other.county))
        if self.country != other.country:
            diffs['country'] = (str(self.country), str(other.country))
        if self.changes != other.changes:
            diffs['changes'] = (str(self.changes), str(other.changes))
        if self.stage != other.stage:
            diffs['stage'] = (str(self.stage), str(other.stage))
        if self.classification != other.classification:
            diffs['classification'] = (str(self.classification), str(other.classification))
        if self.is_variable_cover != other.is_variable_cover:
            diffs['is_variable_cover'] = (str(self.is_variable_cover), str(other.is_variable_cover))
        if self.num_methods != other.num_methods:
            diffs['num_methods'] = (str(self.num_methods), str(other.num_methods))
        if self.num_principles != other.num_principles:
            diffs['num_principles'] = (str(self.num_principles), str(other.num_principles))
        if self.num_variants != other.num_variants:
            diffs['num_variants'] = (str(self.num_variants), str(other.num_variants))
        if self.method != other.method:
            diffs['method'] = (str(self.method), str(other.method))
        if self.title != other.title:
            diffs['title'] = (str(self.title), str(other.title))
        if self.composer != other.composer:
            diffs['composer'] = (str(self.composer), str(other.composer))
        if self.composition_note != other.composition_note:
            diffs['composition_note'] = (str(self.composition_note), str(other.composition_note))
        if self.composition_url != other.composition_url:
            diffs['composition_url'] = (str(self.composition_url), str(other.composition_url))
        if self.detail != other.detail:
            diffs['detail'] = (str(self.detail), str(other.detail))
        if self.duration != other.duration:
            diffs['duration'] = (str(self.duration), str(other.duration))
        if self.event_url != other.event_url:
            diffs['event_url'] = (str(self.event_url), str(other.event_url))
        if self.muffles != other.muffles:
            diffs['muffles'] = (str(self.muffles), str(other.muffles))
        for i, (method, changes) in enumerate(self.methods):
            if i >= len(other.methods):
                diffs[f'methods[{i}]'] = (f'{method} {changes}', 'None')
            elif (method, changes) != other.methods[i]:
                diffs[f'methods[{i}]'] = (f'{method} {changes}', f'{other.methods[i][0]} {other.methods[i][1]}')
        for i, footnote in enumerate(self.footnotes):
            if i >= len(other.footnotes):
                diffs[f'footnotes[{i}]'] = (str(footnote), 'None')
            elif footnote != other.footnotes[i]:
                diffs[f'footnotes[{i}]'] = (str(footnote), str(other.footnotes[i]))
        return diffs

    @classmethod
    def get(cls, id: int = None, bellboard_id: int = None) -> Peal:
        if id:
            key = f'D{id}'
        elif bellboard_id:
            key = f'B{bellboard_id}'
        else:
            raise ValueError('Either database or BellBoard ID must be specified')
        if id is None and bellboard_id is None:
            raise ValueError('Either peal database ID or Bellboard ID must be specified')
        if (peal := Cache.get_cache().get(cls.__name__, key)) is not None:
            return peal

        query = f'SELECT {",".join(FIELD_LIST)}, id FROM peals WHERE 1=1 '
        params = {}
        if id is not None:
            query += 'AND id = %(id)s '
            params['id'] = id
        if bellboard_id is not None:
            query += 'AND bellboard_id = %(bellboard_id)s '
            params['bellboard_id'] = bellboard_id

        result = Database.get_connection().query(query, params).fetchone()
        if result is None:
            return None

        peal = Peal(*result)
        Cache.get_cache().add(cls.__name__, f'D{peal.id}', peal)
        Cache.get_cache().add(cls.__name__, f'B{peal.bellboard_id}', peal)
        return peal

    @classmethod
    def search(cls,
               date_from: datetime.date = None,
               date_to: datetime.date = None,
               ringer_id: int = None,
               ringer_name: str = None,
               ring_id: int = None,
               tower_id: int = None,
               place: str = None,
               county: str = None,
               dedication: str = None,
               association: str = None,
               bell_type: BellType = None,
               length_type: PealLengthType = None,
               order_descending: bool = True) -> list[Peal]:

        query = f'SELECT {",".join(["peals."+field for field in FIELD_LIST])}, peals.id ' + \
                'FROM peals ' + \
                'LEFT JOIN rings ri ON peals.ring_id = ri.id ' + \
                'LEFT JOIN towers t ON ri.tower_id = t.id ' + \
                'LEFT JOIN associations a ON peals.association_id = a.id ' + \
                'WHERE 1=1 '
        params = {}
        if date_from is not None:
            query += 'AND peals.date >= %(date_from)s '
            params['date_from'] = date_from.strftime('%Y-%m-%d')
        if date_to is not None:
            query += 'AND peals.date <= %(date_to)s '
            params['date_to'] = date_to.strftime('%Y-%m-%d')
        if ringer_id:
            query += 'AND peals.id IN (' + \
                     'SELECT peal_id FROM pealringers pr WHERE pr.peal_id = peals.id ' + \
                     'AND pr.ringer_id = %(ringer_id)s ' + \
                     ')'
            params['ringer_id'] = f'{ringer_id}'
        if ringer_name:
            query += 'AND peals.id IN (' + \
                     'SELECT peal_id FROM pealringers pr WHERE pr.peal_id = peals.id ' + \
                     'LEFT JOIN ringers r ON pr.ringer_id = r.id ' + \
                     'WHERE CONCAT(r.given_names, " ", r.last_name) LIKE %(ringer_name)s ' + \
                     ')'
            params['ringer_name'] = f'%{ringer_name.strip()}%'
        if ring_id is not None:
            query += 'AND ri.id = %(ring_id)s '
            params['ring_id'] = ring_id
        if tower_id is not None:
            query += 'AND t.id = %(tower_id)s '
            params['tower_id'] = tower_id
        if place is not None:
            query += 'AND (' + \
                     '(peals.place LIKE %(place)s) OR ' + \
                     '(peals.sub_place LIKE %(place)s) OR ' + \
                     '(t.place LIKE %(place)s) OR ' + \
                     '(t.sub_place LIKE %(place)s)' + \
                     ')'
            params['place'] = place.strip()
        if county is not None:
            query += 'AND (' + \
                     '(peals.county LIKE %(county)s) OR ' + \
                     '(t.county LIKE %(county)s) ' + \
                     ')'
            params['county'] = county.strip()
        if dedication is not None:
            query += 'AND (' + \
                     '(peals.dedication LIKE %(dedication)s) OR ' + \
                     '(t.dedication LIKE %(dedication)s) ' + \
                     ')'
            params['dedication'] = dedication.strip()
        if association is not None:
            query += 'AND a.name = %(association)s '
            params['association'] = association.strip()
        if length_type is not None:
            if config.get_config('general', 'short_peal_threshold') is not None:
                query += 'AND ((peals.stage >= %(short_peal_threshold)s '
                params['short_peal_threshold'] = config.get_config('general', 'short_peal_threshold')
            if length_type == PealLengthType.TOUCH:
                query += 'AND peals.changes < 1250 '
            elif length_type == PealLengthType.QUARTER_PEAL:
                query += 'AND peals.changes >= 1250 AND peals.changes < 5000 '
            elif length_type == PealLengthType.PEAL:
                query += 'AND peals.changes >= 5000 AND peals.changes < 10000 '
            elif length_type == PealLengthType.LONG_LENGTH:
                query += 'AND peals.changes >= 10000 '
            if config.get_config('general', 'short_peal_threshold') is not None:
                query += ') OR (peals.stage < %(short_peal_threshold)s '
                if length_type == PealLengthType.TOUCH:
                    query += 'AND peals.changes < 1260 '
                elif length_type == PealLengthType.QUARTER_PEAL:
                    query += 'AND peals.changes >= 1260 AND peals.changes < 5040 '
                elif length_type == PealLengthType.PEAL:
                    query += 'AND peals.changes >= 5040 AND peals.changes < 10000 '
                elif length_type == PealLengthType.LONG_LENGTH:
                    query += 'AND peals.changes >= 10000 '
                query += '))'
        if bell_type is not None:
            query += 'AND peals.bell_type = %(bell_type)s '
            params['bell_type'] = bell_type.value
        query += 'ORDER BY peals.date ' + ('DESC' if order_descending else 'ASC')
        results = Database.get_connection().query(query, params).fetchall()
        cached_peals = Cache.get_cache().add_all(cls.__name__, {f'D{result[-1]}': Peal(*result) for result in results})
        Cache.get_cache().add_all(cls.__name__, {f'B{peal.bellboard_id}': peal for peal in cached_peals})
        return cached_peals

    @classmethod
    def get_all(cls) -> list[Peal]:
        results = Database.get_connection().query(f'SELECT {",".join(FIELD_LIST)}, id FROM peals').fetchall()
        cached_peals = Cache.get_cache().add_all(cls.__name__, {f'D{result[-1]}': Peal(*result) for result in results})
        Cache.get_cache().add_all(cls.__name__, {f'B{peal.bellboard_id}': peal for peal in cached_peals})
        return cached_peals

    @classmethod
    def clear_data(cls):
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=0;')
        Database.get_connection().query('TRUNCATE TABLE pealphotos')
        Database.get_connection().query('TRUNCATE TABLE pealfootnotes')
        Database.get_connection().query('TRUNCATE TABLE pealringers')
        Database.get_connection().query('TRUNCATE TABLE pealmethods')
        Database.get_connection().query('TRUNCATE TABLE peals')
        Database.get_connection().commit()
        Database.get_connection().query('SET FOREIGN_KEY_CHECKS=1;')
        Cache.get_cache().clear(cls.__name__)
