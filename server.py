import json
import re
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import math

from mcp.server.fastmcp import FastMCP

# Create our MCP server
mcp = FastMCP("MCP Math Assistant")


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract the second number from the first."""
    return a - b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide the first number by the second."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise a number to a power."""
    result = base**exponent

    if isinstance(result, complex):
        raise ValueError("This calculator supports real results only.")

    if not math.isfinite(result):
        raise ValueError("The result is too large or not finite.")

    return result


@mcp.tool()
def square_root(number: float) -> float:
    """Calculate the square root of a non-negative number."""
    if number < 0:
        raise ValueError("Cannot calculate the real square root of a negative number.")

    return math.sqrt(number)


@mcp.tool()
def modulo(a: float, b: float) -> float:
    """Return the remainder after dividing a by b."""
    if b == 0:
        raise ValueError("Cannot calculate a remainder with a zero divisor.")

    return a % b


@mcp.tool()
def read_google_sheet(
    spreadsheet_id: str,
    range_name: str = "Sheet1!A1:Z100",
) -> dict:
    """Read cell values from a Google spreadsheet. Read-only access only."""

    project_dir = Path(__file__).resolve().parent
    token_file = project_dir / "token.json"

    if not token_file.exists():
        raise ValueError(
            "Google authorization token not found. "
            "Run sheets_test.py and authorize Google Sheets first."
        )

     
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    

    credentials = Credentials.from_authorized_user_file(
        str(token_file),
        scopes=scopes,
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_file.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    if not credentials.valid:
        raise ValueError(
            "Google credentials are invalid. Run sheets_test.py again."
        )

    service = build(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False,
    )

    result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
        )
        .execute()
    )

    return {
        "spreadsheet_id": spreadsheet_id,
        "range": result.get("range", range_name),
        "values": result.get("values", []),
    }

def get_google_sheets_service():
    """Create an authorized Google Sheets API service."""
    project_dir = Path(__file__).resolve().parent
    token_file = project_dir / "token.json"

    if not token_file.exists():
        raise ValueError("token.json is missing. Run sheets_test.py first.")

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_authorized_user_file(
        str(token_file),
        scopes=scopes,
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_file.write_text(credentials.to_json(), encoding="utf-8")

    if not credentials.valid:
        raise ValueError("Google credentials are invalid. Run sheets_test.py again.")

    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


@mcp.tool()
def write_google_sheet_range(
    spreadsheet_id: str,
    range_name: str,
    values_json: str,
) -> dict:
    """Write or replace values in a Google Sheets range.

    values_json must be a JSON array of row arrays.
    Example: [["Apples", 10], ["Oranges", 15]].
    Existing values in the specified range may be overwritten.
    """
    try:
        values = json.loads(values_json)
    except json.JSONDecodeError as exc:
        raise ValueError("values_json must be valid JSON.") from exc

    if (
        not isinstance(values, list)
        or not values
        or any(not isinstance(row, list) for row in values)
    ):
        raise ValueError("Provide a non-empty JSON list of row lists.")

    service = get_google_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        )
        .execute()
    )

    return {
        "status": "success",
        "updated_range": result.get("updatedRange", range_name),
        "updated_rows": result.get("updatedRows", 0),
        "updated_cells": result.get("updatedCells", 0),
    }


@mcp.tool()
def append_google_sheet_row(
    spreadsheet_id: str,
    range_name: str,
    values_json: str,
) -> dict:
    """Append one row to a Google Sheet.

    values_json must be a JSON array of values.
    Example: ["Mangoes", 20].
    Use a range such as Sheet1!A:B.
    """
    try:
        values = json.loads(values_json)
    except json.JSONDecodeError as exc:
        raise ValueError("values_json must be valid JSON.") from exc

    if not isinstance(values, list) or not values:
        raise ValueError("Provide a non-empty JSON list of values.")

    service = get_google_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [values]},
        )
        .execute()
    )

    updates = result.get("updates", {})
    return {
        "status": "success",
        "updated_range": updates.get("updatedRange", range_name),
        "updated_rows": updates.get("updatedRows", 0),
        "updated_cells": updates.get("updatedCells", 0),
    }



@mcp.tool()
def increment_google_sheet_quantity(
    spreadsheet_id: str,
    item_name: str,
    increment: float,
    range_name: str = "Sheet1!A:B",
) -> dict:
    """Increase the quantity of an existing item in a Google Sheet.

    Finds the exact item name in column A, reads its numeric quantity
    from column B, adds increment, updates only that quantity cell,
    and reads the cell back to verify the saved value.
    """
    if not item_name.strip():
        raise ValueError("item_name cannot be empty.")

    if not math.isfinite(increment):
        raise ValueError("increment must be a finite number.")

    # Read the table using the existing MCP tool implementation.
    data = read_google_sheet(spreadsheet_id, range_name)
    rows = data.get("values", [])

    matches = [
        row_index
        for row_index, row in enumerate(rows)
        if len(row) >= 2
        and str(row[0]).strip().casefold() == item_name.strip().casefold()
    ]

    if not matches:
        raise ValueError(f"Item '{item_name}' was not found.")

    if len(matches) > 1:
        raise ValueError(
            f"Multiple rows match '{item_name}'. No changes were made."
        )

    # Convert the returned table row index to a sheet row number.
    # For the current read range A:B, the header is row 1.
    # If the range starts elsewhere, account for its starting row.
    # Use this exact spreadsheet ID for all Google Sheets operations:
    # 1YVjl26DOXL7CM6Oe3PGxzlmjF79kGASUQVqfv3UfTSs
    # Never invent, guess, or substitute a spreadsheet ID.
    # If a Google Sheets tool call fails, clearly report the failure.
    # Never present spreadsheet values as current unless they were returned
    # by a successful tool call during the current request.

    match = re.search(r"![A-Z]+(\d+):", range_name)
    start_row = int(match.group(1)) if match else 1
    sheet_row = start_row + matches[0]

    if matches[0] == 0 and str(rows[0][0]).strip().casefold() == "item":
        raise ValueError("The matched row is the header, not an item.")

    current_raw = rows[matches[0]][1]

    try:
        current_quantity = float(current_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Quantity for '{item_name}' is not numeric: {current_raw!r}"
        ) from exc

    new_quantity = current_quantity + increment

    service = get_google_sheets_service()
    target_cell = f"Sheet1!B{sheet_row}"

    # Update only the quantity cell.
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=target_cell,
        valueInputOption="USER_ENTERED",
        body={"values": [[new_quantity]]},
    ).execute()

    # Read the same cell back from Google Sheets.
    verification = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=target_cell,
        )
        .execute()
    )

    verified_values = verification.get("values", [])

    if not verified_values or not verified_values[0]:
        raise RuntimeError(
            f"Write was attempted, but {target_cell} returned no value."
        )

    try:
        saved_quantity = float(verified_values[0][0])
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Could not verify the saved quantity in {target_cell}."
        ) from exc

    if not math.isclose(saved_quantity, new_quantity, rel_tol=1e-9, abs_tol=1e-9):
        raise RuntimeError(
            f"Verification failed: expected {new_quantity}, "
            f"but the sheet contains {saved_quantity}."
        )

    return {
        "status": "success",
        "item": item_name,
        "previous_quantity": current_quantity,
        "increment": increment,
        "new_quantity": saved_quantity,
        "updated_range": target_cell,
        "verified": True,
    }
if __name__ == "__main__":
    mcp.run()
   