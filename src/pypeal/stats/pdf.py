import os
from reportlab.lib.units import mm

from reportlab.platypus import Table, TableStyle, Paragraph

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors, enums as reportlab_enums
from reportlab.lib.styles import getSampleStyleSheet
from pypeal.entities.peal import PealLengthType

from pypeal.entities.report import Report
from pypeal.stats.report import generate_summary

PAGE_HEIGHT = 210*mm
PAGE_WIDTH = 297*mm

NUM_ROWS = 20

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

    data = generate_summary(report.get_peals())
    if data['count'] == 0:
        return

    canvas = Canvas(path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    for report_length_type in data['types']:
        _generate_peal_length_report(canvas, report, data, report_length_type)
        canvas.showPage()

    canvas.save()


def _generate_peal_length_report(canvas: Canvas, report: Report, data: dict, report_length_type: PealLengthType):

    page = Table(
        [
            [Paragraph(f'{report.name}: {report_length_type}', style=styles.byName['Title']), None],
            [
                Paragraph(f'Top {NUM_ROWS} ringers', style=styles.byName['Heading1']),
                Paragraph(f'Top {NUM_ROWS} conductors', style=styles.byName['Heading1']),
                Paragraph(f'Top {NUM_ROWS} methods', style=styles.byName['Heading1']),
            ],
            [
                _drawTable(['Length', 'Count'],
                           data['types'][report_length_type]['ringers'],
                           NUM_ROWS),
                _drawTable(['Length', 'Count'],
                           data['types'][report_length_type]['conductors'],
                           NUM_ROWS),
                _drawTable(['Length', 'Count'],
                           data['types'][report_length_type]['methods'],
                           NUM_ROWS)
            ]
        ],
        rowHeights=[25*mm, 25*mm, None],
    )
    page.setStyle(TableStyle([
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.aquamarine),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('VALIGN', (0, -1), (-1, -1), 'TOP'),
        ('SPAN', (0, 0), (2, 0)),
    ]))

    page.wrapOn(canvas, PAGE_WIDTH, PAGE_HEIGHT)
    page.drawOn(canvas, 0, PAGE_HEIGHT - page._height)


def _drawTable(headings: list[str],
               data: dict,
               num_rows: int) -> Table:

    table_data = [headings]
    for item, count in data.items():
        table_data.append([str(item), count])
        if len(table_data) >= num_rows:
            break
    table = Table(table_data, colWidths=['50%', '50%'])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.aquamarine),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ]))
    return table
