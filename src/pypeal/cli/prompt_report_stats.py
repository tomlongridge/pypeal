from datetime import datetime
from rich.console import Console
from rich.table import Table

from pypeal import utils
from pypeal.cli.chooser import choose_option
from pypeal.cli.prompt_add_ringer import prompt_find_ringer
from pypeal.cli.prompt_add_tower import prompt_find_tower
from pypeal.cli.prompts import UserCancelled, ask, ask_date, confirm, heading
from pypeal.entities.report import Report
from pypeal.entities.ringer import Ringer
from pypeal.stats.report import generate_summary
from rich import box

from pypeal.entities.tower import Ring, Tower


def prompt_report():
    while True:
        reports = Report.get_all()
        try:
            selected_option = choose_option(['Run report',
                                             'New report',
                                             'Edit report',
                                             'Delete report'],
                                            none_option='Back') if len(reports) > 0 else 2
        except UserCancelled:
            return
        try:
            match selected_option:
                case 1:
                    _report(choose_option(reports, none_option='New report'))
                case 2:
                    _report()
                case 3:
                    _report(choose_option(reports, none_option='Back'), prompt=True)
                case 4:
                    _delete_report(choose_option(reports, none_option='Back'))
                    if len(reports) == 0:
                        break
                case _:
                    break
        except UserCancelled:
            if len(reports) == 0:  # There are no other options, exit the menu
                break
            else:
                continue


def _report(report: Report = None, prompt: bool = False):

    if report is None:
        heading('New report')
        report = Report()

    while True:

        if report.id is None or prompt:
            _create_report(report)

        peals = report.get_peals()

        if len(peals) == 0:
            if confirm('No peals match the report parameters.', confirm_message='Amend search?'):
                prompt = True
                continue
            else:
                return
        else:
            if report.id is None or prompt:
                print(f'{len(peals)} matching peals found.')
                if confirm(None, confirm_message='Save report?'):
                    report.name = ask('Name', default=report.name, required=True)
                    report.commit()
            else:
                print(f'{len(peals)} matching peals in "{report.name}".')
            break

    data = generate_summary(peals, report.ring, report.tower, report.ringer)
    if report.ringer:
        conducted_data = generate_summary(peals, report.ring, report.tower, report.ringer, conducted_only=True)
    else:
        conducted_data = None

    console = Console()

    summary_text = _generate_summary_heading(report.date_from, report.date_to, report.ring, report.tower, report.ringer)
    heading(f'Summary ({summary_text.strip()})' if summary_text else 'Summary')

    summary_data = {}
    conducted_summary_data = {} if conducted_data else None
    for type in data['types']:
        summary_data[type] = data['types'][type]['count']
        if conducted_data and type in conducted_data['types']:
            conducted_summary_data[f'{type}s'] = conducted_data['types'][type]['count']
    console.print(_generate_dict_table([summary_data, conducted_summary_data],
                                       value_name=['Rung' if conducted_data else '',
                                                   'Conducted' if conducted_data else None]))

    while True:

        if len(data['types']) > 1:
            length_type = choose_option(list(data['types'].keys()), title='Show report for', none_option='Back')
            if length_type is None:
                return
        else:
            length_type = list(data['types'].keys())[0]

        heading(f'{length_type} statistics')
        length_type_data = data['types'][length_type]
        if conducted_data and length_type in conducted_data['types']:
            length_type_conducted_data = conducted_data['types'][length_type]
        else:
            length_type_conducted_data = None
        console.print(_generate_peal_length_table(length_type_data, length_type_conducted_data))

        while True:
            match choose_option(['All methods',
                                 'All ringers',
                                 'All conductors',
                                 'All associations'],
                                none_option='Back'):
                case 1:
                    console.print(_generate_dict_table(length_type_data['all_methods'], key_name='Methods'))
                case 2:
                    console.print(_generate_dict_table(length_type_data['ringers'], key_name='Ringers'))
                case 3:
                    console.print(_generate_dict_table(length_type_data['conductors'], key_name='Conductors'))
                case 4:
                    console.print(_generate_dict_table(length_type_data['associations'], key_name='Associations'))
                case None:
                    break
            confirm(None, confirm_message='Press enter to continue')

        if len(data['types']) == 1:
            break


def _generate_summary_heading(date_from: datetime.date,
                              date_to: datetime.date,
                              ring: Ring,
                              tower: Tower,
                              ringer: Ringer) -> str:
    summary_text = ''
    if ringer:
        summary_text += f' for {ringer}'
    if ring:
        summary_text += f' at {ring.tower.name}'
        if ring.description:
            summary_text += f' ({ring.description})'
    elif tower:
        summary_text += f' at {tower.name}'
    if date_from:
        summary_text += f' from {utils.format_date_short(date_from)}'
    if date_to:
        summary_text += f' to {utils.format_date_short(date_to)}'
    return summary_text


def _generate_peal_length_table(data: dict, conducted_data: dict) -> Table:
    table = Table(show_header=False, show_footer=False, padding=0, box=None, expand=True)
    table.add_column(None, justify='left', ratio=1)
    table.add_column(None, justify='center', ratio=1)
    table.add_column(None, justify='right', ratio=1)
    if conducted_data:
        column_names = ['Rung', 'Conducted']
    else:
        column_names = ['']
    table.add_row(
        _generate_dict_table([data['stages'], conducted_data['stages'] if conducted_data else None],
                             key_name='Stage',
                             value_name=column_names),
        _generate_dict_table([data['all_methods'], conducted_data['all_methods'] if conducted_data else None],
                             key_name='Methods',
                             value_name=column_names,
                             max_rows=10),
        _generate_dict_table([_generate_misc_data(data), _generate_misc_data(conducted_data) if conducted_data else None],
                             key_name='Misc',
                             value_name=column_names),
    )
    table.add_row(
        _generate_dict_table(data['ringers'], key_name='Top 10 Ringers', max_rows=10),
        _generate_dict_table(data['conductors'], key_name='Top 10 Conductors', max_rows=10),
        _generate_dict_table(data['associations'], key_name='Top 10 Associations', max_rows=10),
    )
    return table


def _generate_misc_data(data: dict) -> dict:
    misc_data = {}
    for type in data['types']:
        misc_data[str(type)] = data['types'][type]
    for type in data['bell_types']:
        misc_data[str(type)] = data['bell_types'][type]
    if 'muffles' in data:
        for type in data['muffles']:
            misc_data[str(type)] = data['muffles'][type]
    misc_data['First rung'] = utils.format_date_short(data['first'])
    misc_data['Last rung'] = utils.format_date_short(data['last'])
    misc_data['Avg. peal speed'] = utils.get_time_str(data['avg_peal_speed']) if 'avg_peal_speed' in data else None
    misc_data['Avg. duration'] = utils.get_time_str(data['avg_duration']) if 'avg_duration' in data else None
    return misc_data


def _generate_dict_table(data: dict | list[dict], key_name: str = '', value_name: str | list[str] = '', max_rows: int = None) -> Table:

    if type(data) is dict:
        combined_data = data
    else:
        combined_data = {}
        for key in data[0]:
            combined_data[key] = []
            for dataset in data:
                if dataset:
                    combined_data[key].append(dataset.get(key))

    table = Table(show_footer=False, box=box.HORIZONTALS, expand=True)
    table.add_column(key_name, justify='left')

    if type(value_name) is str:
        table.add_column(value_name or '', justify='left')
    else:
        for name in value_name:
            table.add_column(name or '', justify='left')
            if len(table.columns) == len(data) + 1:
                break
    if len(combined_data) == 0:
        table.add_row('None')
    else:
        for key, value in list(combined_data.items())[:max_rows or len(combined_data)]:
            if type(value) is list:
                table.add_row(str(key) if key is not None else '', *[str(v) if v else '' for v in value])
            else:
                table.add_row(str(key) if key is not None else '', str(value) if value else '')
    return table


def _create_report(report: Report):

    if (report.ringer and confirm(f'Ringer: "{report.ringer}"', confirm_message='Replace?', default=False)) \
            or (report.ringer is None and confirm(None, confirm_message='Is the report for a specific ringer?')):
        report.ringer = prompt_find_ringer()

    if ((report.tower or report.ring) and
            confirm(f'Tower: {report.tower or report.ring.tower}', confirm_message='Replace?', default=False)) \
        or ((report.tower is None and report.ring is None) and
            confirm(None, confirm_message='Is the report for a specific tower?')):
        if tower := prompt_find_tower():
            if len(tower.rings) > 1 and confirm(None, confirm_message='Is the report for a specific ring?'):
                report.ring = choose_option(tower.rings, title='Ring', none_option='None')
                report.tower = None
            else:
                report.tower = tower
                report.ring = None

    if ((report.date_from or report.date_to) and
            confirm(f'Dates: {utils.format_date_short(report.date_from) if report.date_from else ""} - ' +
                    f'{utils.format_date_short(report.date_to) if report.date_to else ""}',
                    confirm_message='Replace date range?',
                    default=False)) \
        or ((report.date_from is None and report.date_to is None) and
            confirm(None, confirm_message='Is the report for a specific date range?')):
        report.date_from = ask_date('From', default=report.date_from, required=False)
        report.date_to = ask_date('To', default=report.date_to, min=report.date_from if report.date_from else None, required=False)


def _delete_report(report: Report):
    if confirm(f'Delete report "{report}"?', default=False):
        report.delete()
