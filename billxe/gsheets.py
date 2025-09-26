from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import gspread
from google.oauth2.service_account import Credentials


SHEET_URL = "https://docs.google.com/spreadsheets/d/1SbK_vKUJV7dTzDPmxmlEM-7MXBoh6guGRKU4dWvAiw4"


def get_client() -> gspread.Client:
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS env var not set or file not found."
        )
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return gspread.authorize(credentials)


def open_sheet() -> gspread.Spreadsheet:
    client = get_client()
    return client.open_by_url(SHEET_URL)


def find_worksheet_by_alias(spreadsheet: gspread.Spreadsheet, aliases: List[str]) -> Optional[gspread.Worksheet]:
    titles = [ws.title for ws in spreadsheet.worksheets()]
    for name in aliases:
        if name in titles:
            return spreadsheet.worksheet(name)
    return None


def get_or_create_worksheet(spreadsheet: gspread.Spreadsheet, title: str, headers: List[str]) -> gspread.Worksheet:
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=max(26, len(headers)))
        ws.append_row(headers)
        return ws
    # Ensure headers exist
    existing = ws.row_values(1)
    if existing != headers:
        if not existing:
            ws.append_row(headers)
        else:
            ws.update('A1', [headers])
    return ws


def read_records(ws: gspread.Worksheet) -> List[Dict[str, Any]]:
    rows = ws.get_all_records()
    return rows


def append_record(ws: gspread.Worksheet, record: Dict[str, Any]) -> None:
    headers = ws.row_values(1)
    row = [record.get(h, "") for h in headers]
    ws.append_row(row)


def upsert_record(ws: gspread.Worksheet, key_field: str, record: Dict[str, Any]) -> None:
    headers = ws.row_values(1)
    values = ws.get_all_values()
    if not values:
        ws.append_row(headers)
        values = ws.get_all_values()
    id_index = headers.index(key_field)
    for idx, row in enumerate(values[1:], start=2):
        if len(row) > id_index and row[id_index] == str(record[key_field]):
            new_row = [record.get(h, "") for h in headers]
            ws.update(f"A{idx}", [new_row])
            return
    append_record(ws, record)

