'''
Creates a CSV file that can be imported into google calendar.
'''

# TODO: update README

import csv

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

    print(f"date_and_time {parse_date_and_time(date_str, time_str)}")
    start_dt, end_dt = parse_date_and_time(date_str, time_str)
    if not start_dt or not end_dt:
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
    print("Creating CSV for Spartan Brass events...")
    # Example events
    events = [
        {
            'date': 'Monday, January 5, 2026',
            'time': '7:00 PM',
            'sport': 'mbb',
            'opponent': 'Rival University',
            'band': 'White',
            'conductor': 'John Doe',
            'venue': 'Home Stadium'
        },
        {
            'date': 'Tuesday, January 6, 2026',
            'time': 'TBD',
            'sport': 'vball',
            'opponent': 'City College',
            'band': 'BRASS',
            'conductor': 'Jane Smith',
            'venue': 'Away Arena'
        }
    ]

    write_events_to_csv(events, 'spartan_brass_events_test.csv')


if __name__ == "__main__":
    main()