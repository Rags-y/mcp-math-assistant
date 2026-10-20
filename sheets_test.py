
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

PROJECT_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = PROJECT_DIR / "credentials.json"
TOKEN_FILE = PROJECT_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def main():
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "credentials.json was not found in the project folder."
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        SCOPES,
    )
    credentials = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")

    service = build("sheets", "v4", credentials=credentials)

    spreadsheet_id = input("Enter your Google Sheets spreadsheet ID: ").strip()
    if not spreadsheet_id:
        raise ValueError("Spreadsheet ID cannot be empty.")

    result = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="spreadsheetId,properties.title,sheets.properties",
    ).execute()

    print("\nConnected successfully!")
    print("Spreadsheet:", result["properties"]["title"])
    print("Spreadsheet ID:", result["spreadsheetId"])
    print("\nAvailable sheets:")

    for sheet in result.get("sheets", []):
        properties = sheet["properties"]
        print(f"- {properties['title']} (ID: {properties['sheetId']})")


if __name__ == "__main__":
    main()
