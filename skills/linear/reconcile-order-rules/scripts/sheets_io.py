#!/usr/bin/env python3
"""Shared Google Sheets I/O (OAuth-as-user). Run importers with the venv python:
   ~/Claude/Projects/.venv-sheets/bin/python

Uses the cached spreadsheets-scope token (Credentials/google_sheets_token.json) — reads/writes
existing Sheets by key; it does NOT create Sheets (those are created once via the Drive connector).
"""
import os, csv

CREDS_DIR = os.path.expanduser("~/Claude/Projects/Credentials")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
OAUTH_CLIENT = os.path.join(CREDS_DIR, "google_oauth_client.json")
OAUTH_TOKEN = os.path.join(CREDS_DIR, "google_sheets_token.json")
CHUNK = 10000


def client():
    import gspread
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials.from_authorized_user_file(OAUTH_TOKEN, SCOPES) if os.path.exists(OAUTH_TOKEN) else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            creds = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT, SCOPES).run_local_server(port=0)
        with open(OAUTH_TOKEN, "w") as f:
            f.write(creds.to_json())
    return gspread.authorize(creds)


def write_rows(sh, tab, rows):
    """rows = list of lists (row 1 is the header). Clear/create the tab and write in chunks."""
    import gspread
    try:
        ws = sh.worksheet(tab)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab, rows=max(len(rows) + 10, 10), cols=max(len(rows[0]) if rows else 1, 1))
    ws.clear()
    if not rows:
        return ws
    ws.resize(rows=len(rows), cols=len(rows[0]))
    for i in range(0, len(rows), CHUNK):
        blk = rows[i:i + CHUNK]
        ws.update(range_name=f"A{i + 1}", values=blk, value_input_option="RAW")
    return ws


def write_csv(sh, tab, csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return write_rows(sh, tab, rows)


def read_tab(sh, tab):
    return sh.worksheet(tab).get_all_values()


def delete_default_sheet1(sh):
    try:
        ws = sh.worksheet("Sheet1")
        if len(sh.worksheets()) > 1:
            sh.del_worksheet(ws)
    except Exception:
        pass
