from pypeal import utils
from pypeal.bellboard.listener import PealGeneratorListener
from pypeal.cli.generator import PealGenerator
from pypeal.cli.prompts import ask, ask_date, ask_int, confirm, error
from pypeal.parsers import parse_bell_nums
from pypeal.entities.peal import PealType


class ManualGenerator(PealGenerator):

    def parse(self, listener: PealGeneratorListener):

        listener.new_peal(None)

        listener.association(ask('Association', required=False))
        listener.date(ask_date('Date', default=utils.get_now(), required=True))
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
        if listener.peal.stage:
            expected_num_bells_in_peal = listener.peal.stage.value
            max_expected_num_bells_in_peal = expected_num_bells_in_peal + (1 if expected_num_bells_in_peal % 2 == 1 else 0)
        else:
            expected_num_bells_in_peal = max_expected_num_bells_in_peal = None

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

            listener.ringer(name, bell_nums_in_peal, bell_nums_in_ring, is_conductor, max_expected_num_bells_in_peal)

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
