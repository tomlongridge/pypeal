import datetime
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.chooser import choose_option
from pypeal.cli.generator import PealGenerator
from pypeal.cli.prompts import ask, ask_date, ask_int, confirm, error
from pypeal.parsers import parse_bell_nums
from pypeal.peal import BellType, PealType
from pypeal.tower import Tower


class ManualGenerator(PealGenerator):

    def parse(self, listener: PealGeneratorListener):

        listener.new_peal(None)

        listener.association(ask('Association', required=False))
        bell_type = choose_option([e for e in BellType], title='Bell type', default=BellType.TOWER)
        listener.bell_type(bell_type)
        listener.date(ask_date('Date', default=datetime.date.today(), required=True))
        if bell_type == BellType.TOWER:
            listener.tower(dove_id=self._tower_search().id)
        else:
            listener.location(None, None, None, None)
        listener.changes(ask_int('Number of changes', required=False))
        listener.title(ask('Title', required=True))

        if listener.peal.type != PealType.GENERAL_RINGING:
            listener.method_details(ask('Method details', required=False))
            listener.composition_details(ask('Composer', required=False),
                                         ask('Composition URL', required=False),
                                         ask('Composition note', required=False))

        num_ringers = 1
        last_bell_num_in_peal = None
        last_bell_num_in_ring = None
        found_conductor = False
        expected_num_bells_in_peal = listener.peal.stage.value if listener.peal.stage else None

        while True:

            print(f'Add ringer {num_ringers}:')

            bell_nums_in_ring = bell_nums_in_peal = None
            is_conductor = False

            if listener.peal.type != PealType.GENERAL_RINGING:

                default_bell_nums_in_peal = str(last_bell_num_in_peal + 1) if last_bell_num_in_peal else '1'
                bell_nums_in_peal = []
                while len(bell_nums_in_peal) == 0:
                    try:
                        bell_nums_in_peal = parse_bell_nums(
                            ask('Bell number(s) in peal', default=default_bell_nums_in_peal, required=True),
                            max_bell_num=listener.peal.ring.num_bells if listener.peal.ring else None)
                    except ValueError as e:
                        error(str(e))

                default_bell_nums_in_ring = str(last_bell_num_in_ring + 1) if last_bell_num_in_ring else '1'
                bell_nums_in_ring = []
                while len(bell_nums_in_ring) != len(bell_nums_in_peal):
                    try:
                        bell_nums_in_ring = parse_bell_nums(
                            ask('Bell number(s) in ring', default=default_bell_nums_in_ring, required=True),
                            max_bell_num=listener.peal.ring.num_bells if listener.peal.ring else None)
                    except ValueError as e:
                        error(str(e))

            name = ask('Ringer name', required=True)

            if listener.peal.type != PealType.GENERAL_RINGING:
                is_conductor = confirm(None, confirm_message='Is this ringer the conductor', default=not found_conductor)

            listener.ringer(name, bell_nums_in_peal, bell_nums_in_ring, is_conductor)

            if (expected_num_bells_in_peal is None or bell_nums_in_peal[-1] >= expected_num_bells_in_peal) and \
                    not confirm(None, confirm_message='Add another ringer?', default=False):
                break

            num_ringers += 1
            last_bell_num_in_peal = bell_nums_in_peal[-1] if bell_nums_in_peal else None
            last_bell_num_in_ring = bell_nums_in_ring[-1] if bell_nums_in_ring else None
            found_conductor = found_conductor or is_conductor

        while True:
            if footnote := ask('Footnote', required=False):
                listener.footnote(footnote)
            else:
                break

        listener.end_peal()

    def _tower_search(self) -> Tower:
        tower_str = ask('Dove ID or tower description', required=True)
        tower = None
        if tower_str.isnumeric():
            tower = Tower.get(dove_id=int(tower_str))
        else:
            matched_by_name = Tower.search(place=tower_str)
            if len(matched_by_name) == 1:
                tower = matched_by_name[0]
        while tower is None:
            print('No single tower matched, please refine search')
            matched_by_search = Tower.search(place=ask('Place/sub-place', required=False, default=tower_str),
                                             dedication=ask('Dedication', required=False),
                                             county=ask('County', required=False),
                                             country=ask('Country', required=False),
                                             num_bells=ask_int('Number of bells', required=False),
                                             exact_match=False)
            match len(matched_by_search):
                case 0:
                    print('No towers found')
                case 1:
                    tower = matched_by_search[0]
                case 2:
                    tower = choose_option(matched_by_search, title='Choose tower', none_option='None')
        return tower
