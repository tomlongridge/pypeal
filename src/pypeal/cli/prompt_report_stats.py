from datetime import datetime
from rich.console import Console
from rich.table import Table

from pypeal import config, utils
from pypeal.cli.chooser import choose_option
from pypeal.cli.prompts import confirm, heading
from pypeal.peal import Peal
from pypeal.ringer import Ringer
from pypeal.stats.report import generate_summary
from rich import box

from pypeal.tower import Ring, Tower


def prompt_report_stats():
    date_from = config.get_config('report', 'date_from')
    date_to = config.get_config('report', 'date_to')
    ring_id = config.get_config('report', 'ring_id')
    tower_id = config.get_config('report', 'tower_id')
    ringer_id = config.get_config('report', 'ringer_id')
    peals = Peal.search(date_from=date_from,
                        date_to=date_to,
                        ring_id=ring_id,
                        tower_id=tower_id,
                        ringer_id=ringer_id)
    report = generate_summary(peals, ring_id, tower_id, ringer_id)

    console = Console()

    summary_text = _generate_summary_heading(report, date_from, date_to, ring_id, tower_id, ringer_id)
    heading(f'Summary ({summary_text.strip()})' if summary_text else 'Summary')

    summary_data = {}
    for type in report['types']:
        summary_data[f'{type}s'] = (report['types'][type]['count'],
                                    report['types'][type]['conducted_count'] if ringer_id else None)
    console.print(_generate_dict_table(summary_data,
                                       value_name=('Rung' if ringer_id else 'Count',
                                                   'Conducted' if ringer_id else None)))

    if len(report['types']) > 1:
        length_type = choose_option(list(report['types'].keys()), title='Show report for', none_option='Back')
        if length_type is None:
            return
    else:
        length_type = list(report['types'].keys())[0]

    heading(f'{length_type}s')
    length_type_report = report['types'][length_type]
    console.print(_generate_peal_length_table(length_type_report))

    while True:
        match choose_option(['All methods',
                             'All ringers',
                             'All conductors',
                             'All associations'],
                            none_option='Back'):
            case 1:
                combined_methods = {str(m): v for m, v in length_type_report['methods'].items()} | length_type_report['multimethods']
                console.print(_generate_dict_table(dict(sorted(combined_methods.items(), key=lambda x: (-x[1], x[0])))))
            case 2:
                console.print(_generate_dict_table(length_type_report['ringers'], 'Ringers'))
            case 3:
                console.print(_generate_dict_table(length_type_report['conductors'], 'Conductors'))
            case 4:
                console.print(_generate_dict_table(length_type_report['associations'], 'Associations'))
            case None:
                return
        confirm(None, confirm_message='Press enter to continue')


def _generate_summary_heading(report: dict,
                              date_from: datetime.date,
                              date_to: datetime.date,
                              ring_id: int,
                              tower_id: int,
                              ringer_id: int) -> str:
    summary_text = ''
    if ringer_id:
        summary_text += f' for {Ringer.get(ringer_id).name}'
    if ring_id:
        ring = Ring.get(ring_id)
        summary_text += f' at {ring.tower.name}'
        if ring.description:
            summary_text += f' ({ring.description})'
    elif tower_id:
        summary_text += f' at {Tower.get(tower_id).name}'
    if date_from:
        summary_text += f' from {utils.format_date_short(max(date_from, report["first"]))}'
    if date_to:
        summary_text += f' to {utils.format_date_short(min(date_to, report["last"]))}'


def _generate_peal_length_table(data: dict) -> Table:

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
    misc_data['Avg. peal speed'] = utils.get_time_str(data['avg_peal_speed'])
    misc_data['Avg. duration'] = utils.get_time_str(data['avg_duration'])

    combined_methods = {str(m): v for m, v in data['methods'].items()} | data['multimethods']

    table = Table(show_header=False, show_footer=False, padding=0, box=None, expand=True)
    table.add_column(None, justify='left', ratio=1)
    table.add_column(None, justify='center', ratio=1)
    table.add_column(None, justify='right', ratio=1)
    table.add_row(
        _generate_dict_table(data['stages'], 'Stage'),
        _generate_dict_table(combined_methods, 'Methods', max_rows=10),
        _generate_dict_table(misc_data, 'Misc'),
    )
    table.add_row(
        _generate_dict_table(data['ringers'], 'Top 10 Ringers', max_rows=10),
        _generate_dict_table(data['conductors'], 'Top 10 Conductors', max_rows=10),
        _generate_dict_table(data['associations'], 'Top 10 Associations', max_rows=10),
    )
    return table


def _generate_dict_table(data: dict, key_name: str = '', value_name: str | tuple[str] = 'Count', max_rows: int = None) -> Table:
    table = Table(show_footer=False, box=box.HORIZONTALS, expand=True)
    table.add_column(key_name, justify='left')
    if type(value_name) is str:
        table.add_column(value_name or '', justify='left')
    else:
        for name in value_name:
            table.add_column(name or '', justify='left')
    if len(data) == 0:
        table.add_row('None')
    else:
        for key, value in list(data.items())[:max_rows or len(data)]:
            if type(value) is tuple:
                table.add_row(str(key) if key else '', *[str(v) if v else '' for v in value])
            else:
                table.add_row(str(key) if key else '', str(value) if value else '')
    return table
