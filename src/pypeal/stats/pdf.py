from datetime import datetime
from itertools import zip_longest
import os
from reportlab.lib.units import mm

from reportlab.platypus import Table, TableStyle, Paragraph

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors, enums as reportlab_enums
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from pypeal import utils
from pypeal.entities.peal import PealLengthType

from pypeal.entities.report import Report
from pypeal.entities.ringer import Ringer
from pypeal.entities.tower import Ring
from pypeal.stats.report import generate_summary

PAGE_HEIGHT = 210*mm
PAGE_WIDTH = 297*mm
HEADING_PADDING = 5*mm
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
    tables = []

    tables.extend(_draw_table('Key Stats',
                              _get_key_stats(report, data, report_length_type),
                              column_headings=[None, None],
                              column_widths=['50%', '50%'],
                              number_rows=False))

    tables.extend(_draw_table('Stages',
                              data['types'][report_length_type]['stages'],
                              column_headings=['Stage', 'Count']))

    tables.extend(_draw_table('Top 20 methods',
                              data['types'][report_length_type]['methods'],
                              column_headings=['Method', 'Count'],
                              max_rows=20))

    _draw_table_page(canvas, title, tables)

    if not (report.tower or report.ring):
        tables.extend(_draw_table('Top 20 towers',
                                  data['types'][report_length_type]['towers'],
                                  column_headings=['Tower', 'Count'],
                                  max_rows=20,
                                  item_to_str=lambda t: t.name))

    _draw_table_pages(canvas,
                      title,
                      _draw_table('Top 100 ringers',
                                  data['types'][report_length_type]['ringers'],
                                  column_headings=['Ringer', 'Duration', 'Changes', 'Count'],
                                  column_value_keys=['duration', 'changes', 'count'],
                                  column_widths=['*', 50*mm, 20*mm, 15*mm],
                                  values_to_str=[utils.get_time_str, None, None],
                                  max_rows=100),
                      num_columns_per_page=2)

    _draw_table_pages(canvas,
                      title,
                      _draw_table('Top 100 conductors',
                                  data['types'][report_length_type]['conductors'],
                                  column_headings=['Ringer', 'Count'],
                                  max_rows=100),
                      num_columns_per_page=4)

    if report_length_type >= PealLengthType.PEAL:
        _draw_table_pages(canvas,
                          title,
                          _draw_table('Top 20 associations',
                                      data['types'][report_length_type]['associations'],
                                      ['Ringer', 'Count'],
                                      max_rows=20),
                          num_columns_per_page=2)

    _draw_table_pages(canvas,
                      title + ': By Year',
                      _draw_table(None,
                                  dict(sorted(data['types'][report_length_type]['years'].items())),
                                  column_headings=['Year', 'Count'],
                                  number_rows=False),
                      num_columns_per_page=3)

    _draw_table_page(canvas,
                     title + ': Recent Milestones',
                     _draw_table(None,
                                 _get_milestones(report, data, report_length_type),
                                 column_headings=['Milestone', 'Count'],
                                 max_rows=50,
                                 number_rows=False,
                                 column_widths=[30*mm, '*'],
                                 item_to_str=lambda d: utils.format_date_short(d)))

    if 'bells' in data['types'][report_length_type]:
        for table in _draw_bell_table(report.ring or report.tower.get_active_ring(),
                                      data['types'][report_length_type]['bells'],
                                      max_rows=75):
            _draw_table_page(canvas,
                             f'{report.name}: {report_length_type}s: Bells Rung',
                             [table])


def _draw_table_pages(canvas: Canvas, title: str, tables: list[Table], num_columns_per_page: int = 3):

    while len(tables) > num_columns_per_page:
        _draw_table_page(canvas,
                         title,
                         tables[0:num_columns_per_page])
        tables = tables[num_columns_per_page:]
    if len(tables) > 0:
        # Add remaining tables with none padding to the page
        _draw_table_page(canvas,
                         title,
                         [*tables, *[None] * (num_columns_per_page - len(tables))])


def _draw_table_page(canvas: Canvas, title: str, tables: list[Table]):

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
    sections.append(tables)
    row_heights.append(None)

    page = Table(sections, rowHeights=row_heights)
    page.setStyle(TableStyle(table_styles))

    page.wrapOn(canvas, PAGE_WIDTH, PAGE_HEIGHT)
    page.drawOn(canvas, 0, PAGE_HEIGHT - page._height)
    canvas.showPage()


def _draw_table(title: str,
                data: dict,
                column_headings: list[str] = [None, 'Count'],
                column_value_keys: list[str] = ['count'],
                max_rows: int = None,
                number_rows: bool = True,
                column_widths: list[any] = None,
                item_to_str: callable = None,
                values_to_str: list[callable] = []) -> list[Table]:

    tables = []

    max_rows_in_current_page = MAX_ROWS_PER_PAGE
    if title:
        max_rows_in_current_page -= 4  # remove 4 rows in first page to make space for subheadings

    if not column_widths:
        column_widths = ['*', 20*mm]

    if number_rows:
        column_headings = ['#', *column_headings]
        column_widths = [12*mm, *column_widths]

    data_rows = []
    data_rows.append(column_headings)

    for row_num, item in enumerate(data.keys() if type(data) is dict else data, 1):
        data_row = []
        if number_rows:
            data_row.append(Paragraph(str(row_num)))
        data_row.append(Paragraph(item_to_str(item) if item_to_str else str(item)))
        value = data[item]
        value_strs = []
        if type(value) is int:
            value_strs.append(f'{value:,}')
        elif type(value) is dict:
            for column_key, value_to_str in zip_longest(column_value_keys, values_to_str):
                if value_to_str:
                    value_strs.append(value_to_str(value[column_key]))
                else:
                    value_strs.append(f'{value[column_key]:,}')
        else:
            value_strs.append(str(value))
        for value_str in value_strs:
            data_row.append(Paragraph(value_str, style=ParagraphStyle(name='rhcol', alignment=TA_RIGHT)))
        data_rows.append(data_row)
        if (max_rows and row_num >= max_rows) or len(data_rows) > max_rows_in_current_page or row_num == len(data):

            header_row_style = []
            header_row_offset = 0
            if title:
                data_rows = [[Paragraph(title, style=styles.byName['Heading1'])]] + data_rows
                header_row_style = [
                    ('SPAN', (0, 0), (-1, 0)),
                    ('TOPPADDING', (0, 0), (-1, 0), HEADING_PADDING),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), HEADING_PADDING),
                    ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ]
                header_row_offset = 1
                title = None

            table = Table(data_rows, colWidths=column_widths)
            table.setStyle(TableStyle([
                *header_row_style,
                ('BACKGROUND', (0, header_row_offset), (-1, header_row_offset), colors.aquamarine),
                ('FONT', (0, 0), (-1, -1), 'Helvetica'),
                ('FONT', (0, 0), (-1, header_row_offset), 'Helvetica-Bold'),
                ('ALIGN', (0, header_row_offset), (0, -1), 'LEFT'),
                ('ALIGN', (2 if number_rows else 1, header_row_offset), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, header_row_offset), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, header_row_offset + 1), (-1, -1), [colors.whitesmoke, colors.white])
            ]))
            tables.append(table)

            data_rows = [column_headings]
            max_rows_in_current_page = MAX_ROWS_PER_PAGE
            if max_rows and row_num >= max_rows:
                break

    return tables


def _draw_bell_table(ring: Ring, data: dict, max_rows: int) -> list[Table]:

    bell_columns = []
    for bell_role in ring.bells.keys():
        bell_columns.append(bell_role)

    headings = [['#', 'Ringer', *bell_columns, 'Total']]

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
    for row_num, ringer in enumerate(ringer_bells.keys(), 1):
        table_data.append([Paragraph(str(row_num)), Paragraph(str(ringer)), *[f'{value:,}' for value in ringer_bells[ringer]]])
        if (max_rows and row_num >= max_rows) or len(table_data) > MAX_ROWS_PER_PAGE or row_num == len(ringer_bells):
            table = Table(headings + table_data, colWidths=[10*mm, '*', *([20*mm] * len(bell_columns))])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.aquamarine),
                ('FONT', (0, 0), (-1, -1), 'Helvetica'),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            tables.append(table)
            table_data = []
            if max_rows and row_num >= max_rows:
                break

    return tables


def _get_key_stats(report: Report, data: dict, report_length_type: PealLengthType) -> dict:
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
    if 'duration_avg' in data['types'][report_length_type]:
        stats['Average duration'] = utils.get_time_str(data['types'][report_length_type]['duration_avg'])
    stats[f'First {str(report_length_type).lower()}'] = utils.format_date_full(data['types'][report_length_type]['first'])
    stats[f'Last {str(report_length_type).lower()}'] = utils.format_date_full(data['types'][report_length_type]['last'])
    return stats


def _get_milestones(report: Report, data: dict, report_length_type: PealLengthType) -> dict[datetime.date, str]:

    report_data = data['types'][report_length_type]

    milestones = {}
    if 'stages' in report_data:
        for stage, stage_data in report_data['stages'].items():
            if 'last_milestone_count' in stage_data:
                milestones[stage_data['last_milestone_date']] = \
                    f'{utils.suffix_number(stage_data["last_milestone_count"])} of {stage}'

    if report_length_type >= PealLengthType.PEAL and 'associations' in report_data:
        for association, association_data in report_data['associations'].items():
            if 'last_milestone_count' in association_data:
                milestones[association_data['last_milestone_date']] = \
                    f'{utils.suffix_number(association_data["last_milestone_count"])} for the {association}'

    if 'methods' in report_data:
        for method, method_data in report_data['methods'].items():
            if 'last_milestone_count' in method_data:
                milestones[method_data['last_milestone_date']] = \
                    f'{utils.suffix_number(method_data["last_milestone_count"])} of {method}'

    if 'towers' in report_data:
        for tower, tower_data in report_data['towers'].items():
            if 'last_milestone_count' in tower_data:
                milestones[tower_data['last_milestone_date']] = \
                    f'{utils.suffix_number(tower_data["last_milestone_count"])} at {tower.name}'

    if 'ringers' in report_data:
        for ringer, ringer_data in report_data['ringers'].items():
            if 'last_milestone_count' in ringer_data:
                milestones[ringer_data['last_milestone_date']] = \
                    f'{utils.suffix_number(ringer_data["last_milestone_count"])} {"with" if report.ringer else "for"} {ringer}'

    return dict(sorted(milestones.items(), reverse=True))
