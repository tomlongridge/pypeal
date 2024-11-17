from datetime import datetime
import logging
import os.path
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from pypeal import utils
from pypeal.entities.peal import Peal, PealRinger
from pypeal.entities.report import Report

PERMISSION_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = "1TzanU26xBpfDvAdYEG2AcX4Bm5Chflv2u0q5mrzE5gU"

NAMED_RANGE_ALL_PEALS = "all"
NAMED_RANGE_TOWERS = "towers"


class GoogleSheetsError(Exception):
    pass


_logger = logging.getLogger('pypeal')


def update_sheets():
    report: Report
    try:
        for report in Report.get_all():
            _update_sheet(report)
    except HttpError as e:
        _logger.error(f'Unable to connect to Google Sheets: {e.error_details}', e)
        raise GoogleSheetsError('Unable to connect to Google Sheets')


def _update_sheet(report: Report):

    peals = report.get_peals()
    sheet = _get_sheet()

    _update_all_peals(sheet, peals, report)


def _update_all_peals(sheet: Resource, peals: list[Peal], report: Report) -> None:

    existing_range_content, range_location = _get_range(sheet, NAMED_RANGE_ALL_PEALS)
    if not range_location:
        return

    previous_row = _get_header_row(sheet, range_location)

    data = []
    num_cols = len(previous_row[0])
    peal: Peal
    for peal in peals:
        peal_values = []
        for column_name in previous_row[0]:
            value_str = _get_field_value(peal, column_name, report)
            peal_values.append(value_str)
        data.append(peal_values)

    if existing_range_content:
        _clear_range(sheet, _get_rest_of_column_range(range_location, num_cols))
    _update_range(sheet, _get_expanded_range(range_location, num_cols, len(data)), data)


# def _update_towers(sheet: Resource, peals: list[Peal], report: Report) -> None:

#     existing_range_content, range_location = _get_range(sheet, NAMED_RANGE_TOWERS)
#     if not range_location:
#         return

#     previous_row = _get_header_row(sheet, range_location)
    
#     Database.query('SELECT tower')


def _get_header_row(sheet: Resource, range_location: str) -> list[str]:
    sheet_name, col, row = _get_range_breakdown(range_location)
    previous_row, _ = _get_range(sheet, f'{sheet_name}!{col}{row-1}:{row-1}')
    return previous_row


def _authenticate() -> Credentials:

    creds = None

    if os.path.exists(".google/token.json"):
        creds = Credentials.from_authorized_user_file(".google/token.json", PERMISSION_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(".google/credentials.json", PERMISSION_SCOPES)
            creds = flow.run_local_server(port=0)

        with open(".google/token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def _get_sheet() -> Resource:
    service: Resource = build("sheets", "v4", credentials=_authenticate())
    return service.spreadsheets()


def _get_range(sheet: Resource, range_name: str) -> tuple[list[list[str]], str]:
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    except HttpError as e:
        _logger.error(f'Range {range_name} not found', e)
    return result.get("values", []), result.get("range")


def _update_range(sheet: Resource, range_name: str, values: list[list[str]]) -> None:
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body={
            "values": values
        }
    ).execute()


def _clear_range(sheet: Resource, range_name: str) -> None:
    sheet.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()


def _get_range_breakdown(range: str) -> tuple[str, str, int]:
    sheet, cell = range.split("!")
    cell_match = re.match(r'([A-Z]+)([0-9]+)', cell)
    return sheet, cell_match.group(1), int(cell_match.group(2))


def _get_expanded_range(range: str, num_cols: int, num_rows: int) -> str:
    sheet, col, row = _get_range_breakdown(range)
    return f'{sheet}!{col}{row}:{chr(ord(col) + num_cols - 1)}{row + num_rows}'


def _get_rest_of_column_range(range: str, num_cols: int = 1) -> str:
    sheet, col, row = _get_range_breakdown(range)
    return f'{sheet}!{col}{row}:{chr(ord(col) + num_cols - 1)}'


def _get_field_value(peal: Peal, column_name: str, report: Report) -> str:

    field_name = _col_name_to_field_name(column_name)
    if not field_name:
        return None

    match field_name:
        case 'peal_bell' | 'tower_bell':
            if report.ringer:
                peal_ringer: PealRinger
                for peal_ringer in peal.ringers:
                    if peal_ringer.ringer.id == report.ringer.id:
                        if field_name == 'peal_bell':
                            return utils.get_bell_label(peal_ringer.bell_nums)
                        elif peal.ring and peal_ringer.bell_ids:
                            return utils.get_bell_label([peal.ring.get_bell_by_id(bell_id).role for bell_id in peal_ringer.bell_ids])
                        else:
                            return None
                if ringer := peal.get_ringer_by_id(report.ringer.id):
                    return ringer.name
                return 'unknown ringer'
            return 'invalid field'

    if not hasattr(peal, field_name):
        return 'unknown field'

    return _get_value_as_str(getattr(peal, field_name, None))


def _get_value_as_str(value: any) -> str:
    if value is None:
        return None
    if type(value) is bool:
        return 'Yes' if value else 'No'
    if type(value) is datetime.date:
        return value.strftime('%Y-%m-%d')
    if type(value) is list:
        return ', '.join([_get_value_as_str(item) for item in value])
    return str(value)


def _col_name_to_field_name(col_name: str) -> str:
    if not col_name:
        return None
    if '(' in col_name:  # Allow parentheses for descriptions/units
        col_name = re.sub(r'\(.*?\)', '', col_name)
        col_name = col_name.replace('  ', ' ')
    return col_name.strip().lower().replace(" ", "_")
