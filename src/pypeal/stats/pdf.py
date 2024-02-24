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
    stats['Average duration'] = utils.get_time_str(data['types'][report_length_type]['avg_duration'])
    stats[f'First {str(report_length_type).lower()}'] = utils.format_date_full(data['types'][report_length_type]['first'])
    stats[f'Last {str(report_length_type).lower()}'] = utils.format_date_full(data['types'][report_length_type]['last'])
    tables.append(_draw_table(['Stat', None], stats))

    sub_headings.append('Stages')
    tables.append(_draw_table(['Stage', 'Count'],
                              data['types'][report_length_type]['stages']))

    sub_headings.append('Top 20 methods')
    tables.append(_draw_table(['Method', 'Count'],
                              data['types'][report_length_type]['methods'],
                              20))

    if not (report.tower or report.ring):
        sub_headings.append('Top 20 towers')
        tables.append(_draw_table(['Tower', 'Count'],
                                  data['types'][report_length_type]['towers'],
                                  20,
                                  lambda t: t.name))

    sub_headings.append('Top 20 ringers')
    tables.append(_draw_table(['Ringer', 'Count'],
                              data['types'][report_length_type]['ringers'],
                              20))

    sub_headings.append('Top 20 conductors')
    tables.append(_draw_table(['Ringer', 'Count'],
                              data['types'][report_length_type]['conductors'],
                              20))

    if report_length_type >= PealLengthType.PEAL:
        sub_headings.append('Top 20 associations')
        tables.append(_draw_table(['Ringer', 'Count'],
                                  data['types'][report_length_type]['associations'],
                                  20))

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
                data: dict,
                num_rows: int = None,
                item_to_str: callable = None,
                value_to_str: callable = None) -> Table:

    table_data = [headings]
    for item, value in data.items():
        if value_to_str is not None:
            value_str = value_to_str(value)
        elif type(value) is int:
            value_str = f'{value:,}'
        else:
            value_str = str(value)
        table_data.append([Paragraph(item_to_str(item) if item_to_str else str(item)), value_str])
        if num_rows and len(table_data) >= num_rows:
            break
    table = Table(table_data, colWidths=['*', 20*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.aquamarine),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return table


def _draw_bell_table(ring: Ring, data: dict) -> list[Table]:

    bell_columns = []
    for bell_role in ring.bells.keys():
        bell_columns.append(bell_role)

    headings = [['Ringer', *bell_columns, 'Total']]

    ringer_bells: dict[Ringer, list[int]] = dict()
    bell_data: dict[Ringer, int]
    for bell_role, bell_data in data.items():
        for ringer, count in bell_data.items():
            if ringer not in ringer_bells:
                ringer_bells[ringer] = [0] * len(bell_columns)
            ringer_bells[ringer][bell_columns.index(bell_role)] = count

    for counts in ringer_bells.values():
        counts.append(sum(counts))

    tables = []
    table_data = []
    ringer_bells = dict(sorted(ringer_bells.items(), key=lambda x: (-x[1][-1], str(x[0]))))
    for ringer, counts in ringer_bells.items():
        table_data.append([Paragraph(str(ringer)), *[f'{value:,}' for value in counts]])
        if len(table_data) > 26:
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
