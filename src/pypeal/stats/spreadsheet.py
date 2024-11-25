import logging
import re

import pandas as pd

from pypeal.entities.peal import Peal, PealRinger
from pypeal.entities.report import Report
from pypeal.stats.gsheet import GoogleSheetsError, GSheet
from pypeal.stats.pandas import df_to_sheet_data, peal_to_df

SPREADSHEET_ID = "1TzanU26xBpfDvAdYEG2AcX4Bm5Chflv2u0q5mrzE5gU"

NAMED_RANGE_ALL_PEALS = "all"
NAMED_RANGE_TOWERS = "towers"


_logger = logging.getLogger('pypeal')


def update_sheets():
    report: Report
    try:
        for report in Report.get_all():
            _update_sheet(report)
    except GoogleSheetsError as e:
        _logger.error('Unable to connect to Google Sheets', e)


def _update_sheet(report: Report):

    peals = pd.DataFrame([peal_to_df(peal) for peal in report.get_peals()])
    sheet = GSheet(SPREADSHEET_ID)

    _update_all_peals_range(sheet, peals, report)


def _update_all_peals_range(sheet: GSheet, peals: pd.DataFrame, report: Report) -> None:

    if report.ringer:
        peal_bells = []
        tower_bells = []
        for peal_data in peals.itertuples():
            peal: Peal = peal_data[-1]
            peal_ringer: PealRinger
            ringer_peal_bells: str = None
            ringer_tower_bells: str = None
            for peal_ringer in peal.ringers:
                if peal_ringer.ringer.id == report.ringer.id:
                    ringer_peal_bells = peal_ringer.get_peal_bell_labels()
                    ringer_tower_bells = peal_ringer.get_ring_bell_labels(peal.ring)
                    break
            peal_bells.append(ringer_peal_bells)
            tower_bells.append(ringer_tower_bells)
        peals['peal_bell'] = peal_bells
        peals['tower_bell'] = tower_bells

    existing_range_content, range_location = sheet.get_range(NAMED_RANGE_ALL_PEALS)
    if not range_location:
        return

    previous_row = sheet.get_row_at(range_location, offset=-1)

    filtered_data = pd.DataFrame()
    for sheet_column in previous_row[0]:
        column_name = _col_name_to_field_name(sheet_column)
        if column_name in peals.columns:
            filtered_data[sheet_column] = peals[column_name]
        else:
            filtered_data[sheet_column] = None

    num_cols = len(previous_row[0])
    data = df_to_sheet_data(filtered_data)

    if existing_range_content:
        sheet.clear_range(GSheet.get_rest_of_column_range(range_location, num_cols))
    sheet.update_range(GSheet.get_expanded_range(range_location, num_cols, len(data)), data)


def _col_name_to_field_name(col_name: str) -> str:
    if not col_name:
        return None
    if '(' in col_name:  # Allow parentheses for descriptions/units
        col_name = re.sub(r'\(.*?\)', '', col_name)
        col_name = col_name.replace('  ', ' ')
    return col_name.strip().lower().replace(" ", "_")
