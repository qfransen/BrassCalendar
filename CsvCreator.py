'''
Creates a CSV file that can be imported into google calendar.
'''

# TODO: update README

import csv
from datetime import datetime

from calendar_helpers import (
    get_calltime_from_starttime,
    get_endtime_from_starttime,
    create_title_description,
    parse_date_and_time,
)


# Fields that we can populate in the CSV
CSV_FIELDS = [
    "Subject",  # required
    "Start Date",  # required - 05/30/2020
    "Start Time",  # 10:00 AM
    "End Date",
    "End Time",
    "All Day Event",  # True/False
    "Description",
    "Location",
    "Private",  # True/False
]

def create_csv_row(event):
    """
    Given an event dictionary, create a CSV row dictionary.
    :param event: dict with keys like 'date', 'time', 'sport', 'opponent', etc.
    :return: dict representing a CSV row
    """
    date_str = event.get('date', '')
    time_str = event.get('time', '')
    sport = event.get('sport', '')
    opponent = event.get('opponent', '')
    band = event.get('band', '')
    conductor = event.get('conductor', '')
    location = event.get('venue', 'TBD')

    # print(f"date_and_time {parse_date_and_time(date_str, time_str)}")
    datetime = parse_date_and_time(date_str, time_str)
    if not datetime:
        print(f'Unable to create CSV row for event on {date_str} at {time_str}')
        return None  # Invalid date/time

    # extract after determining we got a correct value
    start_dt, end_dt = datetime
    if start_dt is None or end_dt is None:
        print(f'Unable to create CSV row for event on {date_str} at {time_str}')
        return None  # Invalid date/time

    call_time = get_calltime_from_starttime(start_dt.time(), sport)
    end_time = get_endtime_from_starttime(start_dt.time(), sport)

    title, description = create_title_description(
        sport, opponent, band, conductor, call_time, start_dt.time()
    )

    csv_row = {
        "Subject": title,
        "Start Date": start_dt.strftime("%m/%d/%Y"),
        "Start Time": call_time.strftime("%I:%M %p"),
        "End Date": end_dt.strftime("%m/%d/%Y"),
        "End Time": end_time.strftime("%I:%M %p"),
        "All Day Event": "False",
        "Description": description,
        "Location": location,
        "Private": "True",
    }

    # Temporarily handle 'TBD' time as all-day event
    if time_str == 'TBD':
        csv_row["Start Time"] = ""
        csv_row["End Time"] = ""
        csv_row["All Day Event"] = "True"

    return csv_row


def write_events_to_csv(events, csv_filename):
    """
    Write a list of event dictionaries to a CSV file.
    :param events: list of event dicts
    :param csv_filename: output CSV file name
    """

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for event in events:
            csv_row = create_csv_row(event)
            if csv_row:
                writer.writerow(csv_row)


#########################

def main():
    start_load_date = datetime(year=2026, month=1, day=10) # only load in events for this semester
    print(start_load_date)

    # Load in the brass calendar CSV
    file_name = '25-26 Brass Schedule - White Band.csv'
    print(f"Loading Brass Calendar from {file_name} starting at {start_load_date}...")

    with open(file_name, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        print("headers:", reader.fieldnames)

        events = []

        for row in reader:
            event = {}
            event['date'] = row.get('Date', '')
            event['time'] = row.get('Time', '')
            event['sport'] = row.get('Sport', '')
            event['opponent'] = row.get('Event', '')
            event['band'] = row.get('Band', '')
            event['conductor'] = row.get('Conductor', '')
            event['venue'] = row.get('Venue', '')

            # Only include events on or after start_load_date
            date_str = event['date']
            time_str = event['time']
            dt = parse_date_and_time(date_str, time_str)
            if not dt:
                print(f'Unable to parse date/time for event on {date_str} at {time_str}')
                continue
            date, _ = dt
            if not date:
                print(f'Unable to parse date for event on {date_str}')
                continue
            if date >= start_load_date:
                events.append(event)

    print(f"Loaded {len(events)} events from Brass Calendar.")
    write_events_to_csv(events, 'white_brass_events-test-1-7-26.csv')


if __name__ == "__main__":
    main()