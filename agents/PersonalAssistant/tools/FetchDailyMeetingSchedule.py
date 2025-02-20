from smolagents import Tool
from pydantic import Field
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly'
]

class FetchDailyMeetingSchedule(Tool):
    name = "fetch_daily_meetings"
    description = """
    Retrieves calendar events for a specific date using Google Calendar API.
    Uses OAuth authentication and token.json for credentials.
    Returns a formatted string containing meeting details including time, location, and description."""
    inputs = {
        "date": {
            "type": "string",
            "description": "The date to fetch meetings for in YYYY-MM-DD format. If not provided, defaults to today.",
            "default": None,
            "nullable": True,
        }
    }
    output_type = "string"

    def forward(self, date: str = None):
        creds = None
        if os.path.exists('token.json'):
            try:
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            except Exception as e:
                return f"Error loading credentials: {str(e)}"

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    return f"Error refreshing credentials: {str(e)}"
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    return f"Error in authentication flow: {str(e)}"

            try:
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                return f"Error saving credentials: {str(e)}"

        try:
            # Build the Calendar service
            service = build('calendar', 'v3', credentials=creds)

            # Get the date to fetch events for
            if date:
                target_date = datetime.strptime(date, '%Y-%m-%d')
            else:
                target_date = datetime.now()

            # Set time boundaries for the target date
            timezone = pytz.timezone('UTC')  # You can change this to your local timezone
            start_time = timezone.localize(datetime.combine(target_date, datetime.min.time()))
            end_time = timezone.localize(datetime.combine(target_date, datetime.max.time()))

            # Get events
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            if not events:
                return f"No meetings scheduled for {target_date.strftime('%Y-%m-%d')}."

            meeting_details = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Convert to datetime objects for formatting
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
                # Format the event details
                event_str = (
                    f"Meeting: {event['summary']}\n"
                    f"Time: {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}\n"
                )
                
                # Add location if available
                if 'location' in event:
                    event_str += f"Location: {event['location']}\n"
                
                # Add description if available
                if 'description' in event:
                    event_str += f"Description: {event['description']}\n"
                
                meeting_details.append(event_str)

            return "\n".join(meeting_details)

        except Exception as e:
            return f"Error accessing Google Calendar API: {str(e)}"

if __name__ == "__main__":
    tool = FetchDailyMeetingSchedule()
    print(tool.forward(date="2024-02-17")) 