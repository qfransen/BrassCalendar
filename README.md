# Spartan Brass Calendar Creator

## Current Overview
The CsvCreator creates a CSV which can be imported into Google Calendar.
It loads in the data from a CSV file and manipulates it into
the correct format for Google Calendar.
I'm hoping this makes it easy for me to create a updateable google calendar in the future
by building upon this script.

# Future Plans

## How to Use
Request access here: 

[More information about importing calendars into Google Calendar](https://support.google.com/calendar/answer/37100?hl=en&co=GENIE.Platform%3DDesktop)


## Technical Details
This is a python script that grabs rows from an online google sheet
to create calendar events for Spartan Brass.
One of the necessary requirements is an ability to update events.
The goal of this script is to be able to update the calendar whenever this script is run,
and to create a calendar that multiple people can subscribe to.