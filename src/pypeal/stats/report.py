from pypeal.entities.peal import Peal, PealLengthType, PealRinger
from pypeal.entities.ringer import Ringer
from pypeal.entities.tower import Bell, Ring, Tower


def generate_global_summary(peals: list[Peal]) -> dict:
    report = {}
    report['count'] = len(peals)
    report['unsubmitted_count'] = 0
    report['types'] = dict()
    report['last_added'] = None
    for peal in peals:
        if report['last_added'] is None or report['last_added'] < peal.created_date:
            report['last_added'] = peal.created_date
        if peal.length_type not in report['types']:
            report['types'][peal.length_type] = 0
        report['types'][peal.length_type] += 1
        if peal.type >= PealLengthType.QUARTER_PEAL:
            if peal.bellboard_id is None:
                report['unsubmitted_count'] += 1
    _sort_table(report['types'])
    return report


def generate_summary(peals: list[Peal],
                     ring: Ring = None,
                     tower: Tower = None,
                     ringer: Ringer = None,
                     conducted_only: bool = False) -> dict:

    report = {}
    report['count'] = len(peals)
    report['types'] = dict()
    report['first'] = None
    report['last'] = None
    report['last_added'] = None
    for peal in peals:

        if ringer and conducted_only:
            ringer_is_conductor = False
            for peal_ringer in peal.ringers:
                if peal_ringer.ringer.id == ringer.id:
                    ringer_is_conductor = peal_ringer.is_conductor
                    break
            if not ringer_is_conductor:
                continue

        peal_length_data = _add_peal(report, 'types', peal.length_type, peal)

        _add_peal(peal_length_data, 'types', peal.type, peal)
        _add_peal(peal_length_data, 'bell_types', peal.bell_type, peal)
        _add_peal(peal_length_data, 'years', peal.date.year, peal)
        _add_peal(peal_length_data, 'days_of_year', peal.date.strftime("%m-%d"), peal)

        if peal.association:
            _add_peal(peal_length_data, 'associations', peal.association, peal)

        if peal.stage:
            _add_peal(peal_length_data, 'stages', peal.stage, peal)

        if peal.method:
            _add_peal(peal_length_data, 'methods', peal.method, peal)

        _add_peal(peal_length_data, 'titles', peal.title, peal)

        if peal.muffles:
            _add_peal(peal_length_data, 'muffles', peal.muffles, peal)

        for peal_ringer in peal.ringers:
            if ringer and ringer == peal_ringer.ringer:
                continue
            _add_peal(peal_length_data, 'ringers', peal_ringer.ringer, peal)
            if peal_ringer.is_conductor:
                _add_peal(peal_length_data, 'conductors', peal_ringer.ringer, peal)

        if peal.ring:

            if not ring:
                _add_peal(peal_length_data, 'rings', peal.ring, peal)
                if peal.ring not in peal_length_data['rings']:
                    peal_length_data['rings'][peal.ring] = dict()

            if not tower:
                _add_peal(peal_length_data, 'towers', peal.ring.tower, peal)

            if ring or tower:
                if 'bells' not in peal_length_data:
                    peal_length_data['bells'] = dict()
                # Add counts of ringers on each bell
                peal_ringer: PealRinger
                for peal_ringer in peal.ringers:
                    if peal_ringer.bell_ids is None:
                        continue
                    for bell_id in peal_ringer.bell_ids:
                        # Get the role of the bell in the ring or current active ring
                        bell_role = None
                        for role, ring_bell in (ring or tower.get_active_ring()).bells.items():
                            if ring_bell.id == Bell.get(bell_id).id:
                                bell_role = role
                        if bell_role is None:
                            raise ValueError(f'Could not find bell role for {bell_id} in {ring or tower}')

                        _add_peal(peal_length_data['bells'], bell_role, peal_ringer.ringer, peal)

    report['types'] = dict(sorted(report['types'].items()))
    for length_type_report in report['types'].values():
        _sort_table(length_type_report, ['count', 'changes'])

    return report


def _add_peal(data: dict, section: str, key: any, peal: Peal) -> dict:

    if section not in data:
        data[section] = dict()

    if key not in data[section]:
        selected_dict = data[section][key] = dict()
        selected_dict['count'] = 0
        selected_dict['first'] = peal.date
        selected_dict['last'] = peal.date
        selected_dict['changes'] = 0
        selected_dict['duration'] = None
        selected_dict['_duration_recorded_count'] = 0
    else:
        selected_dict = data[section][key]

    selected_dict['count'] += 1
    if peal.date < selected_dict['first']:
        selected_dict['first'] = peal.date
    if peal.date > selected_dict['last']:
        selected_dict['last'] = peal.date
    if peal.changes:
        selected_dict['changes'] += peal.changes
    if peal.duration:
        if selected_dict['duration'] is None:
            selected_dict['duration'] = 0
        selected_dict['duration'] += peal.duration
        selected_dict['_duration_recorded_count'] += 1
        selected_dict['duration_avg'] = selected_dict['duration'] / selected_dict['_duration_recorded_count']
    if (peal.changes or peal.duration) and selected_dict['changes'] > 0 and selected_dict['duration'] is not None:
        selected_dict['peal_speed_avg'] = (selected_dict['duration'] / selected_dict['changes']) * 5000

    if selected_dict['count'] % 25 == 0:
        selected_dict['last_milestone_count'] = selected_dict['count']
        if 'last_milestone_date' not in selected_dict or peal.date > selected_dict['last_milestone_date']:
            selected_dict['last_milestone_date'] = peal.date

    selected_dict['next_milestone_count'] = (selected_dict['count'] // 25) + 25 - selected_dict['count'] % 25

    return selected_dict


def _sort_table(table: dict, sort_keys: list[str] = []) -> None:
    def _sort_func(x: tuple) -> tuple:
        if type(x[1]) is int:
            return -x[1], str(x[0])
        elif type(x[1]) is dict:
            sort_elements = []
            for sort_key in sort_keys:
                if sort_key in x[1]:
                    sort_elements.append(-x[1][sort_key])
            sort_elements.append(str(x[0]))
            return tuple(sort_elements)
        else:
            return (str(x[0]))

    # Sort tables that contain just dict with a named key or int values and recurse down into nested tables
    for report_name, nested_reports in table.items():
        if type(nested_reports) is dict:
            countable_table = True
            for value in nested_reports.values():
                if type(value) is dict:
                    if not set(value.keys()).issuperset(set(sort_keys)):
                        countable_table = False
                    _sort_table(nested_reports, sort_keys)
                elif type(value) is not int:
                    countable_table = False
            if countable_table:
                table[report_name] = dict(sorted(nested_reports.items(), key=_sort_func))
