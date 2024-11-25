import logging
import os.path
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

PERMISSION_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsError(Exception):
    pass


_logger = logging.getLogger('pypeal')


class GSheet:

    def __init__(self, worksheet_id: str):
        if not (credentials := self.__authenticate()):
            raise GoogleSheetsError('Unable to authenticate with Google Sheets')

        service: Resource = build("sheets", "v4", credentials=credentials)
        self.__values = service.spreadsheets().values()
        self.__worksheet_id = worksheet_id

    def get_range(self, range_name: str) -> tuple[list[list[str]], str]:
        try:
            result = self.__values.get(
                spreadsheetId=self.__worksheet_id,
                range=range_name
            ).execute()
        except HttpError as e:
            _logger.error(f'Range {range_name} not found', e)
        return result.get("values", []), result.get("range")

    def update_range(self, range_name: str, values: list[list[str]]) -> None:
        self.__values.update(
            spreadsheetId=self.__worksheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={
                "values": values
            }
        ).execute()

    def clear_range(self, range_name: str) -> None:
        self.__values.clear(
            spreadsheetId=self.__worksheet_id,
            range=range_name
        ).execute()

    def get_row_at(self, range_location: str, offset: int = 0) -> list[str]:
        sheet_name, col, row = GSheet.get_range_breakdown(range_location)
        row_data, _ = self.get_range(f'{sheet_name}!{col}{row + offset}:{row + offset}')
        return row_data

    @staticmethod
    def get_range_breakdown(range: str) -> tuple[str, str, int]:
        sheet, cell = range.split("!")
        cell_match = re.match(r'([A-Z]+)([0-9]+)', cell)
        return sheet, cell_match.group(1), int(cell_match.group(2))

    @staticmethod
    def get_expanded_range(range: str, num_cols: int, num_rows: int) -> str:
        sheet, col, row = GSheet.get_range_breakdown(range)
        return f'{sheet}!{col}{row}:{chr(ord(col) + num_cols - 1)}{row + num_rows}'

    @staticmethod
    def get_rest_of_column_range(range: str, num_cols: int = 1) -> str:
        sheet, col, row = GSheet.get_range_breakdown(range)
        return f'{sheet}!{col}{row}:{chr(ord(col) + num_cols - 1)}'

    def __authenticate(self) -> Credentials:

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
