from smolagents import Tool
from pydantic import Field
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import json

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly'
]

class GetUnreadEmails(Tool):
    name = "get_unread_emails"
    description = """
    Retrieves unread emails from Gmail using OAuth authentication.
    The tool saves the authentication token in 'token.json' for future use.
    Returns a formatted string containing email details including sender, subject, and date."""
    inputs = {
        "max_results": {
            "type": "integer",
            "description": "Maximum number of unread emails to retrieve",
            "default": 10,
            "nullable": True,
        }
    }
    output_type = "string"

    def forward(self, max_results: int = 10):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists('token.json'):
            try:
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            except Exception as e:
                return f"Error loading credentials: {str(e)}"

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    return f"Error refreshing credentials: {str(e)}"
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials_web.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    return f"Error in authentication flow: {str(e)}"
                
            # Save the credentials for the next run
            try:
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                return f"Error saving credentials: {str(e)}"

        try:
            # Build the Gmail service
            service = build('gmail', 'v1', credentials=creds)

            # Get unread messages
            results = service.users().messages().list(
                userId='me',
                labelIds=['UNREAD'],
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                return "No unread messages found."

            email_details = []
            for message in messages:
                msg = service.users().messages().get(
                    userId='me', 
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No date')

                email_details.append(f"From: {sender}\nSubject: {subject}\nDate: {date}\n")

            return "\n".join(email_details)

        except Exception as e:
            return f"Error accessing Gmail API: {str(e)}"

if __name__ == "__main__":
    tool = GetUnreadEmails()
    print(tool.forward(max_results=5)) 