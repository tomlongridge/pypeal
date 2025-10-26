import logging
import re

import pandas as pd

from pypeal.entities.peal import Peal, PealRinger
from pypeal.entities.report import Report
from pypeal.entities.ringer import Ringer
from pypeal.stats.gsheet import GoogleSheetsError, GSheet
from pypeal.stats.pandas import df_to_sheet_data, peal_to_df

NAMED_RANGE_PREFIX = "pypeal"
NAMED_RANGE_PREFIX_ALL_PEALS = "all_peals"
NAMED_RANGE_PREFIX_PEAL_COUNT = "peal_count"
NAMED_RANGE_PREFIX_RINGER_COUNT = "ringer_count"


class UnrecgonizedColumnError(Exception):
    def __init__(self, column: str):
        super().__init__(f'Column "{column}" not found')


_logger = logging.getLogger('pypeal')


def update_sheets():
    report: Report
    try:
        for report in Report.get_all():
            _update_sheet(report)
    except GoogleSheetsError as e:
        _logger.error('Unable to connect to Google Sheets', e)


def _update_sheet(report: Report):

    if not report.spreadsheet_id:
        _logger.info(f'Skipping report "{report.name}" - no associated spreadsheet ID')
        return

    _logger.info(f'Locating spreadsheet for report "{report.name}"')
    sheet = GSheet(report.spreadsheet_id)
    _logger.info(f'Updating spreadsheet "{sheet.name}" at {sheet.url}')

    _logger.info('Getting peal data')
    peals = pd.DataFrame([peal_to_df(peal) for peal in report.get_peals()])

    for range_name in sheet.get_named_ranges():

        if not range_name.startswith(NAMED_RANGE_PREFIX):
            continue

        _logger.info(f'Updating range "{range_name}"')

        existing_range_content, range_location = sheet.get_range(range_name)

        if not (headers := _get_headers(sheet, range_location)):
            _logger.info('No headers for range')
            continue

        data: pd.DataFrame = None
        if range_name.startswith(f"{NAMED_RANGE_PREFIX}_{NAMED_RANGE_PREFIX_ALL_PEALS}"):
            data = _update_all_peals_range(headers, peals, report)
        elif range_name.startswith(f"{NAMED_RANGE_PREFIX}_{NAMED_RANGE_PREFIX_PEAL_COUNT}"):
            data = _update_peal_breakdown_range(headers, peals, report)
        elif range_name.startswith(f"{NAMED_RANGE_PREFIX}_{NAMED_RANGE_PREFIX_RINGER_COUNT}"):
            data = _update_ringers_range(headers, peals, report)

        _logger.debug(f'Converting {len(data)} rows to sheet data')
        row_data = df_to_sheet_data(data)

        if not row_data:
            _logger.info('No peal data for range')
            continue

        if existing_range_content:
            _logger.debug(f'Clearing existing range content: {range_location} for {len(row_data[0])} columns')
            sheet.clear_range(GSheet.get_rest_of_column_range(range_location, len(row_data[0])))
        _logger.debug(f'Setting range content: {range_location} for {len(row_data[0])} columns and {len(row_data)} rows')
        sheet.update_range(GSheet.get_expanded_range(range_location, len(row_data[0]), len(row_data)), row_data)

        _logger.info(f'Updated range "{range_name}"')


def _update_all_peals_range(headers: list[str], peals: pd.DataFrame, report: Report) -> pd.DataFrame:

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

    return _filter_data(peals, headers)


def _update_peal_breakdown_range(headers: list[str], peals: pd.DataFrame, report: Report) -> pd.DataFrame:
    return _filter_data(peals, headers).value_counts().reset_index()


def _update_ringers_range(headers: list[str], peals: pd.DataFrame, report: Report) -> pd.DataFrame:

    # Explode list of ringers (so one row per ringer per peal)
    ringers_view = peals.explode('ringers')

    # Use column names from spreadsheet based on ringer fields
    used_columns = []
    for field in [_col_name_to_field_name(header) for header in headers]:
        if hasattr(Ringer, field):
            ringers_view[field] = ringers_view['ringers'].apply(lambda r: getattr(r.ringer, field))
            used_columns.append(field)
        else:
            raise UnrecgonizedColumnError(field)

    # Exclude the report ringer from stats (they will always be in it)
    if report.ringer:
        ringers_view = ringers_view[ringers_view.apply(lambda r: r['ringers'].id != report.ringer.id, axis=1)]

    # Group by the selected columns and count
    return ringers_view.groupby(used_columns) \
        .size().reset_index(name='count') \
        .sort_values('count', ascending=False)


# Get a list of strings representing the headers of the previous row, until the first empty cell and excluding an optional final 'count'
def _get_headers(sheet: GSheet, range_location: str) -> list[str]:
    headers = []
    previous_row = sheet.get_row_at(range_location, offset=-1)
    if not previous_row:
        return headers
    for header in previous_row[0]:
        if header:
            headers.append(header)
        else:
            break
    if headers[-1].lower() == 'count':
        headers.pop()
    return headers


def _filter_data(data: pd.DataFrame, headers: list[str]) -> pd.DataFrame:
    filtered_data = pd.DataFrame()
    for sheet_column in headers:
        column_name = _col_name_to_field_name(sheet_column)
        if column_name in data.columns:
            filtered_data[sheet_column] = data[column_name]
        else:
            _logger.warning(f'Column "{column_name}" not found')
            filtered_data[sheet_column] = None
    return filtered_data


def _col_name_to_field_name(col_name: str) -> str:
    if not col_name:
        return None
    if '(' in col_name:  # Allow parentheses for descriptions/units
        col_name = re.sub(r'\(.*?\)', '', col_name)
        col_name = col_name.replace('  ', ' ')
    return col_name.strip().lower().replace(" ", "_")
