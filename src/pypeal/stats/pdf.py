import datetime
import os
from reportlab.lib.units import mm

from reportlab.platypus import Table, TableStyle, Paragraph

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors, enums as reportlab_enums
from reportlab.lib.styles import getSampleStyleSheet
from pypeal import utils
from pypeal.entities.peal import PealLengthType

from pypeal.entities.report import Report
from pypeal.entities.ringer import Ringer
from pypeal.entities.tower import Ring
from pypeal.stats.report import generate_summary

PAGE_HEIGHT = 210*mm
PAGE_WIDTH = 297*mm

MAX_ROWS_PER_PAGE = 27

styles = getSampleStyleSheet()
styles.byName['Title'].fontSize = 24
styles.byName['Title'].leading = 32
styles.byName['Heading1'].alignment = reportlab_enums.TA_CENTER


def generate_reports() -> list[str]:

    reports_dir = os.path.join(os.getcwd(), 'reports')

    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)

    reports = []
    for report in Report.get_all():
        report_path = os.path.join(reports_dir, f'{report.name.replace(" ", "-")}.pdf')
        if report.enabled:
            _generate_report(report, report_path)
            reports.append(report_path)

    return reports


def _generate_report(report: Report, path: str):

    data = generate_summary(report.get_peals(), report.ring, report.tower, report.ringer)
    if data['count'] == 0:
        return

    canvas = Canvas(path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    for report_length_type in data['types']:
        if report_length_type >= PealLengthType.QUARTER_PEAL:
            _generate_peal_length_report(canvas, report, data, report_length_type)

    canvas.save()


def _generate_peal_length_report(canvas: Canvas, report: Report, data: dict, report_length_type: PealLengthType):

    title = f'{report.name}: {report_length_type}s'
    sub_headings = []
    tables = []

    sub_headings.append('Key Stats')
    stats = {}
    stats[f'Total {str(report_length_type).lower()}s'] = data['types'][report_length_type]['count']
    stats['Total number of changes'] = f'{data["types"][report_length_type]["changes"]:,}'
    stats['Number of methods'] = len(data['types'][report_length_type]['methods'])
    if not (report.tower or report.ring):
        stats['Number of towers'] = len(data['types'][report_length_type]['towers'])
    stats['Number of ringers'] = len(data['types'][report_length_type]['ringers'])
    stats['Number of conductors'] = len(data['types'][report_length_type]['conductors'])
    busiest_year_pair = next(iter(data['types'][report_length_type]['years'].items()))
    stats['Busiest year'] = f'{busiest_year_pair[0]} ({busiest_year_pair[1]["count"]})'
    stats['Average duration'] = utils.get_time_str(data['types'][report_length_type]['avg_duration'])
    stats[f'First {str(report_length_type).lower()}'] = utils.format_date_full(data['types'][report_length_type]['first'])
    stats[f'Last {str(report_length_type).lower()}'] = utils.format_date_full(data['types'][report_length_type]['last'])
    tables.extend(_draw_table(['Stat', ''], stats, number_rows=False))

    sub_headings.append('Stages')
    tables.extend(_draw_table(['Stage', 'Count'],
                              data['types'][report_length_type]['stages']))

    sub_headings.append('Top 20 methods')
    tables.extend(_draw_table(['Method', 'Count'],
                              data['types'][report_length_type]['methods'],
                              20))

    if not (report.tower or report.ring):
        sub_headings.append('Top 20 towers')
        tables.extend(_draw_table(['Tower', 'Count'],
                                  data['types'][report_length_type]['towers'],
                                  20,
                                  lambda t: t.name))

    sub_headings.append('Top 20 ringers')
    tables.extend(_draw_table(['Ringer', 'Count'],
                              data['types'][report_length_type]['ringers'],
                              20))

    sub_headings.append('Top 20 conductors')
    tables.extend(_draw_table(['Ringer', 'Count'],
                              data['types'][report_length_type]['conductors'],
                              20))

    if report_length_type >= PealLengthType.PEAL:
        sub_headings.append('Top 20 associations')
        tables.extend(_draw_table(['Ringer', 'Count'],
                                  data['types'][report_length_type]['associations'],
                                  20))

    by_year_data = dict(sorted(data['types'][report_length_type]['years'].items()))
    by_year_tables = _draw_table(['Year', 'Count'], by_year_data, number_rows=False)
    sub_headings.append('By year')
    sub_headings.extend([''] * (len(by_year_tables) - 1))
    tables.extend(by_year_tables)

    sub_headings.append('By day of year')
    tables.extend(_draw_table(['Day'], _get_missing_days_of_year(data['types'][report_length_type]['days_of_year']), number_rows=False))

    while len(tables) > 3:
        _draw_table_page(canvas, title, sub_headings[0:3], tables[0:3])
        sub_headings = sub_headings[3:]
        tables = tables[3:]
    if len(tables) > 0:
        _draw_table_page(canvas, title, sub_headings, tables)

    if data['types'][report_length_type]['bells']:
        for table in _draw_bell_table(report.ring or report.tower.get_active_ring(), data['types'][report_length_type]['bells']):
            _draw_table_page(canvas,
                             f'{report.name}: {report_length_type}s: Bells Rung',
                             None,
                             [table])


def _draw_table_page(canvas: Canvas, title: str, sub_headings: list[str], tables: list[Table]):

    sections = [[Paragraph(title, style=styles.byName['Title'])]]
    row_heights = [25*mm]
    table_styles = [
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.aquamarine),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('VALIGN', (0, -1), (-1, -1), 'TOP'),
        ('SPAN', (0, 0), (-1, 0)),
    ]
    if sub_headings:
        sections.append([Paragraph(text, style=styles.byName['Heading1']) for text in sub_headings])
        row_heights.append(25*mm)
    sections.append(tables)
    row_heights.append(None)

    page = Table(sections, rowHeights=row_heights)
    page.setStyle(TableStyle(table_styles))

    page.wrapOn(canvas, PAGE_WIDTH, PAGE_HEIGHT)
    page.drawOn(canvas, 0, PAGE_HEIGHT - page._height)
    canvas.showPage()


def _draw_table(headings: list[str],
                data: dict | list,
                max_rows: int = None,
                number_rows: bool = True,
                item_to_str: callable = None,
                value_to_str: callable = None) -> list[Table]:

    tables = []
    if number_rows:
        data_rows = [['#', *headings]]
        column_widths = [10*mm, '*', 20*mm]
    else:
        data_rows = [headings]
        column_widths = ['*', 20*mm]
    max_rows_in_current_page = MAX_ROWS_PER_PAGE - 4  # remove 4 rows in first page to make space for subheadings
    for row_num, item in enumerate(data.keys() if type(data) is dict else data, 1):
        data_row = []
        if number_rows:
            data_row.append(Paragraph(str(row_num)))
        data_row.append(Paragraph(item_to_str(item) if item_to_str else str(item)))
        if type(data) is dict:
            value = data[item]
            if value_to_str is not None:
                value_str = value_to_str(value)
            elif type(value) is int:
                value_str = f'{value:,}'
            elif type(value) is dict and 'count' in value:
                value_str = f'{value["count"]:,}'
            else:
                value_str = str(value)
            data_row.append(value_str)
        data_rows.append(data_row)
        if (max_rows and row_num >= max_rows) or len(data_rows) > max_rows_in_current_page or row_num == len(data):
            table = Table(data_rows, colWidths=column_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.aquamarine),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONT', (0, 0), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
            ]))
            tables.append(table)
            data_rows = [headings]
            max_rows_in_current_page = MAX_ROWS_PER_PAGE
            if max_rows and row_num >= max_rows:
                break
    return tables


def _draw_bell_table(ring: Ring, data: dict) -> list[Table]:

    bell_columns = []
    for bell_role in ring.bells.keys():
        bell_columns.append(bell_role)

    headings = [['Ringer', *bell_columns, 'Total']]

    ringer_bells: dict[Ringer, list[int]] = dict()
    bell_data: dict[Ringer, int]
    for bell_role, bell_data in data.items():
        for ringer, ringer_data in bell_data.items():
            if ringer not in ringer_bells:
                ringer_bells[ringer] = [0] * len(bell_columns)
            ringer_bells[ringer][bell_columns.index(bell_role)] = ringer_data['count']

    for counts in ringer_bells.values():
        counts.append(sum(counts))

    tables = []
    table_data = []
    ringer_bells = dict(sorted(ringer_bells.items(), key=lambda x: (-x[1][-1], str(x[0]))))
    for ringer, counts in ringer_bells.items():
        table_data.append([Paragraph(str(ringer)), *[f'{value:,}' for value in counts]])
        if len(table_data) > MAX_ROWS_PER_PAGE - 3:
            table = Table(headings + table_data, colWidths=['*', *([20*mm] * len(bell_columns))])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.aquamarine),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONT', (0, 0), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            tables.append(table)
            table_data = []

    return tables


def _get_missing_days_of_year(data: dict) -> list[str]:
    missing_days = []
    for day in range(1, 366):
        key = (datetime.date(2000, 1, 1) + datetime.timedelta(days=day)).strftime("%m-%d")
        if key not in data:
            missing_days.append(key)
    return missing_days
