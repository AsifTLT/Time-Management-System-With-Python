from __future__ import print_function

import datetime
import os.path
import sys
import sqlite3
import pytz

from dateutil import parser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    if len(sys.argv) < 2:
        print("Usage: python quickstart.py <add|commit> [duration description]")
        sys.exit(1)

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    command = sys.argv[1]
    if command == "add":
        if len(sys.argv) < 4:
            print("Usage: python quickstart.py add <duration> <description>")
            sys.exit(1)
        duration = sys.argv[2]
        description = sys.argv[3]
        addEvent(creds, duration, description)
    elif command == "commit":
        commitHours(creds)
    else:
        print("Invalid command. Use 'add' or 'commit'.")
        sys.exit(1)

def commitHours(creds):
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        today = datetime.date.today()
        timeStart = str(today) + "T10:00:00+06:00"
        timeEnd = str(today) + "T23:59:59+06:00" 
        print("Getting Today's Coding Hours...")
        events_result = service.events().list(calendarId="aa00f55b0132c2bf81e78148fe96d26862ed2ba8b215b173fb50064edca65eb0@group.calendar.google.com", timeMin=timeStart, timeMax=timeEnd, singleEvents=True, orderBy="startTime", timeZone="Asia/Dhaka").execute()
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return
        
        total_duration = datetime.timedelta(
            seconds=0,
            minutes=0,
            hours=0
        )
        print("CODING HOURS:")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
              
            start_formatted = parser.isoparse(start)
            end_formatted = parser.isoparse(end)
            duration = end_formatted - start_formatted
              
            total_duration += duration
            print(f"{event['summary']}, duration: {duration}")
        print(f"Total Coding Time: {total_duration}")
        
        conn = sqlite3.connect("hours.db")
        cur = conn.cursor()
        print("Opened database successfully")
        date = datetime.date.today()
        
        formatted_total_duration = total_duration.total_seconds() / 3600
        coding_hours = (date, 'CODING', formatted_total_duration)
        cur.execute("INSERT INTO hours VALUES (?, ?, ?);", coding_hours)
        conn.commit()
        print("Coding Hours added to the database successfully")
          
    except HttpError as error:
        print(f"An error occurred: {error}")

def addEvent(creds, duration, description):
    start = datetime.datetime.now()
    end = start + datetime.timedelta(hours=int(duration))
    start_formatted = start.isoformat() + 'Z'
    end_formatted = end.isoformat() + 'Z'
    
    event = {
        'summary': description,
        'start': {
            'dateTime': start_formatted,
            'timeZone': 'Asia/Dhaka',
        },
        'end': {
            'dateTime': end_formatted,
            'timeZone': 'Asia/Dhaka',
        },
    }

    service = build('calendar', 'v3', credentials=creds)
    event = service.events().insert(calendarId="aa00f55b0132c2bf81e78148fe96d26862ed2ba8b215b173fb50064edca65eb0@group.calendar.google.com", body=event).execute()
    print(f'Event created: {event.get("htmlLink")}')

if __name__ == "__main__":
    main()
