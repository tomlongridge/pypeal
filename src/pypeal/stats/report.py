from pypeal.entities.method import Stage
from pypeal.entities.peal import Peal, PealRinger, PealType
from pypeal.entities.ringer import Ringer
from pypeal.entities.tower import Bell, Ring, Tower


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

        if peal.length_type not in report['types']:
            report['types'][peal.length_type] = dict()
            report['types'][peal.length_type]['count'] = 0
            report['types'][peal.length_type]['first'] = peal.date
            report['types'][peal.length_type]['last'] = peal.date
            report['types'][peal.length_type]['changes'] = 0
            report['types'][peal.length_type]['duration'] = 0
            report['types'][peal.length_type]['bell_types'] = dict()
            report['types'][peal.length_type]['types'] = dict()
            report['types'][peal.length_type]['associations'] = dict()
            report['types'][peal.length_type]['stages'] = dict()
            report['types'][peal.length_type]['methods'] = dict()
            report['types'][peal.length_type]['all_methods'] = dict()
            report['types'][peal.length_type]['muffles'] = dict()
            report['types'][peal.length_type]['ringers'] = dict()
            report['types'][peal.length_type]['conductors'] = dict()
            report['types'][peal.length_type]['rings'] = dict()
            report['types'][peal.length_type]['towers'] = dict()
        else:
            if peal.date < report['types'][peal.length_type]['first']:
                report['types'][peal.length_type]['first'] = peal.date
            if peal.date > report['types'][peal.length_type]['last']:
                report['types'][peal.length_type]['last'] = peal.date

        report['types'][peal.length_type]['count'] += 1
        if peal.changes:
            report['types'][peal.length_type]['changes'] += peal.changes
        if peal.duration:
            report['types'][peal.length_type]['duration'] += peal.duration

        if peal.type not in report['types'][peal.length_type]['types']:
            report['types'][peal.length_type]['types'][peal.type] = 0
        report['types'][peal.length_type]['types'][peal.type] += 1

        if peal.bell_type not in report['types'][peal.length_type]['bell_types']:
            report['types'][peal.length_type]['bell_types'][peal.bell_type] = 0
        report['types'][peal.length_type]['bell_types'][peal.bell_type] += 1

        if peal.association:
            if peal.association not in report['types'][peal.length_type]['associations']:
                report['types'][peal.length_type]['associations'][peal.association] = 0
            report['types'][peal.length_type]['associations'][peal.association] += 1

        if peal.stage:
            if peal.stage not in report['types'][peal.length_type]['stages']:
                report['types'][peal.length_type]['stages'][peal.stage] = 0
            report['types'][peal.length_type]['stages'][peal.stage] += 1

        if peal.method:
            if peal.method not in report['types'][peal.length_type]['methods']:
                report['types'][peal.length_type]['methods'][peal.method] = 0
            report['types'][peal.length_type]['methods'][peal.method] += 1
            if peal.num_methods_in_title == 0:
                if peal.method.full_name not in report['types'][peal.length_type]['all_methods']:
                    report['types'][peal.length_type]['all_methods'][peal.method.full_name] = 0
                report['types'][peal.length_type]['all_methods'][peal.method.full_name] += 1
            else:
                mixed_description = 'Spliced ' if peal.type == PealType.SPLICED_METHODS else 'Mixed '
                if peal.classification:
                    mixed_description += f'{peal.classification} '
                if peal.is_variable_cover:
                    mixed_description += f'{Stage(peal.stage.value - 1)} and '
                mixed_description += str(peal.stage)
                if mixed_description not in report['types'][peal.length_type]['all_methods']:
                    report['types'][peal.length_type]['all_methods'][mixed_description] = 0
                report['types'][peal.length_type]['all_methods'][mixed_description] += 1

        if peal.muffles:
            if peal.muffles not in report['types'][peal.length_type]['muffles']:
                report['types'][peal.length_type]['muffles'][peal.muffles] = 0
            report['types'][peal.length_type]['muffles'][peal.muffles] += 1

        for peal_ringer in peal.ringers:
            if peal_ringer.ringer not in report['types'][peal.length_type]['ringers']:
                report['types'][peal.length_type]['ringers'][peal_ringer.ringer] = 0
            report['types'][peal.length_type]['ringers'][peal_ringer.ringer] += 1
            if peal_ringer.is_conductor:
                if peal_ringer.ringer.name not in report['types'][peal.length_type]['conductors']:
                    report['types'][peal.length_type]['conductors'][peal_ringer.ringer.name] = 0
                report['types'][peal.length_type]['conductors'][peal_ringer.ringer.name] += 1

        if peal.ring:

            if peal.ring not in report['types'][peal.length_type]['rings']:
                report['types'][peal.length_type]['rings'][peal.ring] = 0
            report['types'][peal.length_type]['rings'][peal.ring] += 1

            if peal.ring.tower not in report['types'][peal.length_type]['towers']:
                report['types'][peal.length_type]['towers'][peal.ring.tower] = dict()
                report['types'][peal.length_type]['towers'][peal.ring.tower]['count'] = 0
                report['types'][peal.length_type]['towers'][peal.ring.tower]['first'] = peal.date
                report['types'][peal.length_type]['towers'][peal.ring.tower]['last'] = peal.date
                report['types'][peal.length_type]['towers'][peal.ring.tower]['bells'] = dict()
            report['types'][peal.length_type]['towers'][peal.ring.tower]['count'] += 1
            if peal.date < report['types'][peal.length_type]['towers'][peal.ring.tower]['first']:
                report['types'][peal.length_type]['towers'][peal.ring.tower]['first'] = peal.date
            if peal.date > report['types'][peal.length_type]['towers'][peal.ring.tower]['last']:
                report['types'][peal.length_type]['towers'][peal.ring.tower]['last'] = peal.date
            peal_ringer: PealRinger
            for peal_ringer in peal.ringers:
                if peal_ringer.bell_ids is None:
                    continue
                for bell_id in peal_ringer.bell_ids:
                    bell = Bell.get(bell_id)
                    if bell not in report['types'][peal.length_type]['towers'][peal.ring.tower]['bells']:
                        report['types'][peal.length_type]['towers'][peal.ring.tower]['bells'][bell] = dict()
                    if peal_ringer.ringer not in report['types'][peal.length_type]['towers'][peal.ring.tower]['bells'][bell]:
                        report['types'][peal.length_type]['towers'][peal.ring.tower]['bells'][bell][peal_ringer.ringer] = 0
                    report['types'][peal.length_type]['towers'][peal.ring.tower]['bells'][bell][peal_ringer.ringer] += 1

    report['types'] = dict(sorted(report['types'].items()))
    for length_type_report in report['types'].values():
        if length_type_report['duration']:
            if length_type_report['changes']:
                length_type_report['avg_peal_speed'] = (length_type_report['duration'] / length_type_report['changes']) * 5040
            length_type_report['avg_duration'] = length_type_report['duration'] / length_type_report['count']
        _sort_table(length_type_report)

    return report


def _sort_table(table: dict) -> None:
    # Sort tables that contain just int values and recurse down into nested tables
    for report_name, nested_reports in table.items():
        if type(nested_reports) is dict:
            all_numeric = True
            for value in nested_reports.values():
                if type(value) is not int:
                    all_numeric = False
                    if type(value) is dict:
                        _sort_table(nested_reports)
            if all_numeric:
                table[report_name] = dict(sorted(nested_reports.items(), key=lambda x: (-x[1], str(x[0]))))
