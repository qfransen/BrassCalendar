from datetime import datetime, timedelta, time
import re

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
        print('Error parsing date:', date_str)
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

    # Check for time range
    if '-' in time_str:
        start_str, end_str = time_str.split('-', 1)
        start_time = parse_time(start_str)
        end_time = parse_time(end_str)
        if not start_time or not end_time:
            print('Error parsing time range:', time_str)
            return None, None
    else:
        # Just a start time - default duration of 0.5 hours
        start_time = parse_time(time_str)
        if not start_time:
            print('Error parsing start time:', time_str)
            return None, None
        # Default duration of 0.5 hours
        start_datetime = datetime.combine(date_obj, start_time)
        end_datetime = (start_datetime + timedelta(hours=0.5))

        return start_datetime, end_datetime

def get_calltime_from_starttime(start_time, game_type):
    """Given a start time and game type, return an appropriate call time."""
    gt = game_type.lower()
    if gt == 'vball' or gt == 'hoc':
        return (datetime.combine(datetime.today(), start_time) - timedelta(minutes=20)).time()
    if gt == 'mbb':
        return (datetime.combine(datetime.today(), start_time) - timedelta(minutes=45)).time()
    if gt == 'wbb':
        return (datetime.combine(datetime.today(), start_time) - timedelta(minutes=30)).time()
    return (datetime.combine(datetime.today(), start_time) - timedelta(minutes=0)).time()

def get_endtime_from_starttime(start_time, game_type):
    # print('get_endtime', start_time, type(start_time))
    # print(start_time == time(17, 10), game_type.lower() == 'brass rehearsal', game_type)
    """Given a start time and game type, return an appropriate end time."""
    gt = game_type.lower()
    if gt == 'vball':
        return (datetime.combine(datetime.today(), start_time) + timedelta(hours=2)).time()
    if gt == 'mbb' or gt == 'wbb' or gt == 'hoc':
        return (datetime.combine(datetime.today(), start_time) + timedelta(hours=2, minutes=30)).time()
    if gt == 'rehearsal' and start_time == time(17, 10):  # 50 minute rehearsals in spring
        return (datetime.combine(datetime.today(), start_time) + timedelta(hours=0, minutes=50)).time()
    # fallback
    return (datetime.combine(datetime.today(), start_time) + timedelta(hours=2)).time()

def create_title_description(sport, opponent, band, conductor, calltime, starttime):
    # Convert from military time to standard time strings
    calltime = calltime.strftime("%I:%M %p").lstrip('0')
    starttime = starttime.strftime("%I:%M %p").lstrip('0')

    # No vs for rehearsals
    if sport.lower() == 'rehearsal':
        title = f"Brass - {band}: {sport} @ {starttime}"
    else:
        title = f"Brass - {band}: {sport} vs {opponent} @ {starttime}"

    description = f"Call Time: {calltime}\nStart Time: {starttime}\nConductor: {conductor}"
    return (title, description)

