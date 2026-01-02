import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, time, timedelta
import re

# -----------------------------------------
# Config
SOURCE_SPREADSHEET_ID = 'YOUR_SOURCE_SPREADSHEET_ID_HERE' # The ID of the READ-ONLY sheet containing your event data.
MAPPING_SPREADSHEET_ID = 'YOUR_MAPPING_SPREADSHEET_ID_HERE' # The ID of your OWN, new, writable sheet for tracking Event IDs.
SHEET_NAME = 'Sheet1'  # The name of the sheet in the SOURCE spreadsheet containing the data.
MAPPING_SHEET_NAME = 'EventIDs' # The name of the sheet in the MAPPING spreadsheet for storing IDs.
SOURCE_RANGE = f'{SHEET_NAME}!A2:G'  # Data range (Title through Band/Category)
MAPPING_RANGE = f'{MAPPING_SHEET_NAME}!A2:A' # Range for reading Event IDs (one ID per row, starting at A2).0

CALENDAR_IDS = {
    'all_events': '',
    'white': '',
    'green': ''
}

# The scope defines what the script can access.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/calendar']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'


def authenticate():
    """Shows user consent screen and handles authentication flow."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Error: {CREDENTIALS_FILE} not found. Follow the setup guide.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds


def parse_date_and_time(date_str, time_str):
    """
    Takes the date and time cols to create start time and end time for GCal event.
    :param date_str: Date like "Sunday, October 12, 2025"
    :param time_str: Time like "7:00 PM", "6PM-8PM", "TBD"
    :return: (start_datetime, end_datetime) as datetime objects
    """

    # Remove weekday if present
    date_str = re.sub(r'^[A-Za-z]+,\s*', '', date_str)
    date_fmt = "%B %d, %Y"
    try:
        date_obj = datetime.strptime(date_str, date_fmt)
    except ValueError:
        return None, None

    # Handle TBD for time
    if not time_str or time_str.strip().upper() == 'TBD':
        start_datetime = date_obj.replace(hour=0, minute=0)
        end_datetime = start_datetime + timedelta(hours=1)
        return start_datetime, end_datetime

    # Inner function to parse time
    def parse_time(t):
        t = t.strip().replace(' ', '')
        # Add space before AM/PM if missing
        t = re.sub(r'(\d)(AM|PM|am|pm)', r'\1 \2', t)
        try:
            return datetime.strptime(t, "%I:%M %p").time()
        except ValueError:
            try:
                return datetime.strptime(t, "%I %p").time()
            except ValueError:
                return None

def get_calltime_from_starttime(start_time, game_type):
    """Given a start time and game type, return an appropriate call time."""
    if game_type.lower() == 'vball':
        return (datetime.combine(datetime.today(), start_time) - timedelta(minutes=20)).time()
    if game_type.lower() == 'hoc':
        return (datetime.combine(datetime.today(), start_time) - timedelta(minutes=20)).time()
    if game_type.lower() == 'mbb':
        return (datetime.combine(datetime.today(), start_time) - timedelta(minutes=45)).time()
    if game_type.lower() == 'wbb':
        return (datetime.combine(datetime.today(), start_time) - timedelta(minutes=30)).time()
    return (datetime.combine(datetime.today(), start_time) - timedelta(minutes=00)).time()  # base case, hopefully for rehearsals

def get_endtime_from_starttime(start_time, game_type):
    """Given a start time and game type, return an appropriate end time."""
    if game_type.lower() == 'vball':
        return (datetime.combine(datetime.today(), start_time) + timedelta(hours=2, minutes=00)).time()
    if game_type.lower() == 'mbb' or game_type.lower() == 'wbb':
        return (datetime.combine(datetime.today(), start_time) + timedelta(hours=2, minutes=30)).time()
    if game_type.lower() == 'hoc':
        return (datetime.combine(datetime.today(), start_time) + timedelta(hours=2, minutes=30)).time()
    print(f'Mismatch with game type; get_endtime; {game_type=}')
    return (datetime.combine(datetime.today(), start_time) + timedelta(hours=2)).time()

def create_title_description(sport, opponent, band, conductor, calltime, starttime):
    title = f"Spartan Brass - {band}: {sport} vs {opponent} at {starttime}"
    description = f"Call Time: {calltime}\nStart Time: {starttime}\nConductor: {conductor}"

    return (title, description)


def get_sheet_data(service, spreadsheet_id, range_name):
    """Retrieves data from the specified Google Sheet range, skipping empty rows."""
    try:
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        # Filter out rows that are completely empty to prevent errors
        values = [row for row in result.get('values', []) if any(cell.strip() for cell in row)]

        if not values:
            print(f'No valid data found in spreadsheet ID {spreadsheet_id} at range {range_name}.')
            return []
        return values
    except HttpError as err:
        print(f"An error occurred while accessing the sheet (ID: {spreadsheet_id}, Range: {range_name}): {err}")
        return []


def get_event_id_map(service):
    """Retrieves existing Event IDs from the mapping sheet."""
    try:
        # Get all existing event IDs from the designated mapping sheet
        result = service.spreadsheets().values().get(spreadsheetId=MAPPING_SPREADSHEET_ID,
                                                     range=MAPPING_RANGE).execute()
        # Returns a flat list of IDs, where the list index corresponds to the row index of the data.
        return [row[0] if row else '' for row in result.get('values', [])]
    except HttpError as err:
        print(f"Warning: Could not read event ID mapping sheet. Assuming all events are new. Error: {err}")
        return []


def update_sheet_event_id(service, row_index, event_id):
    """Writes the Google Calendar Event ID back to the MAPPING sheet."""
    # Write to column A of the mapping sheet. Row index 0 in the data list corresponds to row 2 in the sheet.
    update_range = f'{MAPPING_SHEET_NAME}!A{row_index + 2}'

    body = {'values': [[event_id]]}
    try:
        service.spreadsheets().values().update(
            spreadsheetId=MAPPING_SPREADSHEET_ID,
            range=update_range,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        print(f"Wrote Event ID to mapping sheet at row {row_index + 2}.")
    except HttpError as err:
        print(f"An error occurred while updating the mapping sheet: {err}")


# --- Main Logic ---
def sync_events():
    """Reads the sheet and synchronizes events with Google Calendar."""
    creds = authenticate()
    if not creds:
        return

    # Build services
    try:
        sheet_service = build('sheets', 'v4', credentials=creds)
        calendar_service = build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"Could not build Google API services: {e}")
        return

    print("Fetching sheet data...")
    # Rows structure expected: [Title, Date, Start Time, End Time, Description, Location, Band/Category]
    data_rows = get_sheet_data(sheet_service, SOURCE_SPREADSHEET_ID, SOURCE_RANGE)

    if not data_rows:
        return

    print("Reading existing Event IDs from mapping sheet...")
    event_id_map = get_event_id_map(sheet_service)

    print(f"Found {len(data_rows)} rows of data. Starting sync...")

    for i, row in enumerate(data_rows):
        # Ensure row has enough columns (at least 7 columns for Title to Band/Category)
        # Note: Sheets API may return shorter lists for rows with trailing empty cells.
        # We ensure at least 4 core columns are present, and assume the 7th column for band if needed.
        if len(row) < 4:
            print(f"Skipping row {i + 2}: Not enough core data (Title, Date, Start, End).")
            continue

        date_str = row[0]
        title = row[1]
        venue = row[2]
        start_time_str = row[3]
        sport = row[4]
        band = row[5]
        conductor = row[6]
        # description = row[4] if len(row) > 4 else ''
        # location = row[5] if len(row) > 5 else ''
        # band_category = row[6] if len(row) > 6 else 'Master'  # Default to Master if column is blank

        # Get the Event ID from the lookup map based on the row index
        event_id = event_id_map[i] if i < len(event_id_map) else ''

        # Parse date and time
        start_dt = parse_date_and_time(date_str, start_time_str)
        end_dt = parse_date_and_time(date_str, end_time_str)

        if not start_dt or not end_dt:
            print(f"Skipping row {i + 2} ('{title}'): Invalid date/time format.")
            continue

        # Ensure start is before end. If not, adjust to a 1 hour duration.
        if start_dt >= end_dt:
            end_dt = start_dt + timedelta(hours=1)
            # print(f"Warning: Adjusted end time for '{title}' to 1 hour later.")

        # Determine the color ID based on the band category
        # .strip() and .title() ensure matching works even if the user types " green band " or "WHITE BAND"
        color_key = band_category.strip().title()
        color_id = BAND_COLOR_MAP.get(color_key, BAND_COLOR_MAP.get('Master'))

        # Format for Google Calendar API
        event_body = {
            'summary': title,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'America/New_York',  # IMPORTANT: Change to your timezone!
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'America/New_York',  # IMPORTANT: Change to your timezone!
            },
            'colorId': color_id  # Set the color based on the band
        }

        try:
            if event_id:
                # --- UPDATE EXISTING EVENT ---
                try:
                    # Check if event exists (404 if deleted) before attempting patch
                    calendar_service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()

                    # If it exists, patch it (update)
                    calendar_service.events().patch(
                        calendarId=CALENDAR_ID,
                        eventId=event_id,
                        body=event_body
                    ).execute()
                    print(f"Row {i + 2}: Updated existing event '{title}' ({color_key}).")

                except HttpError as e:
                    # If the event was manually deleted from the calendar
                    if e.resp.status == 404:
                        print(f"Row {i + 2}: Event ID {event_id} not found on calendar. Re-creating event.")
                        # Clear the ID in the mapping sheet and proceed to creation logic
                        update_sheet_event_id(sheet_service, i, '')
                        event_id = ''  # Set ID to empty to trigger creation
                    else:
                        raise e  # Re-raise other HTTP errors

            if not event_id:
                # --- CREATE NEW EVENT ---
                created_event = calendar_service.events().insert(
                    calendarId=CALENDAR_ID,
                    body=event_body
                ).execute()

                new_event_id = created_event['id']
                print(f"Row {i + 2}: Created new event '{title}' ({color_key}). New ID: {new_event_id}")

                # Write the new ID back to the MAPPING sheet
                update_sheet_event_id(sheet_service, i, new_event_id)

        except HttpError as err:
            print(f"An error occurred during calendar operation for row {i + 2} ('{title}'): {err}")

    print("\nSync complete! All new/changed events synchronized and color-coded.")


if __name__ == '__main__':
    sync_events()

# Row structure: Date, Event, Venue, Time, Sport, Band, Conductor
