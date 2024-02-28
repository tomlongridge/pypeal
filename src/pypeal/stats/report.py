from pypeal.entities.peal import Peal, PealRinger
from pypeal.entities.ringer import Ringer
from pypeal.entities.tower import Bell, Ring, Tower


def generate_global_summary(peals: list[Peal]) -> dict:
    report = {}
    report['count'] = len(peals)
    report['types'] = dict()
    report['last_added'] = None
    for peal in peals:
        if report['last_added'] is None or report['last_added'] < peal.created_date:
            report['last_added'] = peal.created_date
        if peal.length_type not in report['types']:
            report['types'][peal.length_type] = 0
        report['types'][peal.length_type] += 1
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

        if report['last_added'] is None or report['last_added'] < peal.created_date:
            report['last_added'] = peal.created_date
        if report['first'] is None or report['first'] > peal.date:
            report['first'] = peal.date
        if report['last'] is None or report['last'] < peal.date:
            report['last'] = peal.date

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
        if length_type_report['duration']:
            if length_type_report['changes']:
                length_type_report['avg_peal_speed'] = (length_type_report['duration'] / length_type_report['changes']) * 5040
            length_type_report['avg_duration'] = length_type_report['duration'] / length_type_report['count']
        _sort_table(length_type_report, 'count')

    return report


def _add_peal(data: dict, section: str, key: any, peal: Peal) -> dict:

    if section not in data:
        data[section] = dict()

    if key not in data[section]:
        data[section][key] = dict()
        data[section][key]['count'] = 0
        data[section][key]['first'] = peal.date
        data[section][key]['last'] = peal.date
        data[section][key]['changes'] = 0
        data[section][key]['duration'] = 0

    data[section][key]['count'] += 1
    if peal.date < data[section][key]['first']:
        data[section][key]['first'] = peal.date
    if peal.date > data[section][key]['last']:
        data[section][key]['last'] = peal.date
    if peal.changes:
        data[section][key]['changes'] += peal.changes
    if peal.duration:
        data[section][key]['duration'] += peal.duration
    return data[section][key]


def _sort_table(table: dict, sort_key: str = None) -> None:
    def _sort_func(x: tuple) -> tuple:
        if type(x[1]) is int:
            return -x[1], str(x[0])
        elif type(x[1]) is dict and sort_key is not None and sort_key in x[1]:
            return -x[1][sort_key], str(x[0])
        else:
            return (str(x[0]))

    # Sort tables that contain just dict with a named key or int values and recurse down into nested tables
    for report_name, nested_reports in table.items():
        if type(nested_reports) is dict:
            countable_table = True
            for value in nested_reports.values():
                if type(value) is dict:
                    if sort_key not in value:
                        countable_table = False
                    _sort_table(nested_reports)
                elif type(value) is not int:
                    countable_table = False
            if countable_table:
                table[report_name] = dict(sorted(nested_reports.items(), key=_sort_func))
