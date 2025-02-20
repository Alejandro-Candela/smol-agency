from smolagents import Tool
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64
import mimetypes

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

class SendEmail(Tool):
    name = "send_email"
    description = """
    Sends an email using Gmail API with optional attachments.
    Uses OAuth authentication and token.json for credentials.
    Returns a confirmation message with the email status."""
    inputs = {
        "to": {
            "type": "string",
            "description": "Email address of the recipient",
        },
        "subject": {
            "type": "string",
            "description": "Subject of the email",
        },
        "body": {
            "type": "string",
            "description": "Body content of the email. Can include HTML formatting.",
        },
        "attachments": {
            "type": "array",
            "description": "List of file paths to attach to the email",
            "default": None,
            "nullable": True,
            "items": {
                "type": "string"
            }
        }
    }
    output_type = "string"

    def forward(self, to: str, subject: str, body: str, attachments: list = None):
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
            service = build('gmail', 'v1', credentials=creds)
            
            # Create message container
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject

            # Add body
            message.attach(MIMEText(body, 'html'))

            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        return f"Error: File not found - {file_path}"
                    
                    content_type, encoding = mimetypes.guess_type(file_path)
                    if content_type is None or encoding is not None:
                        content_type = 'application/octet-stream'
                    main_type, sub_type = content_type.split('/', 1)
                    
                    with open(file_path, 'rb') as fp:
                        msg = MIMEBase(main_type, sub_type)
                        msg.set_payload(fp.read())
                    
                    encoders.encode_base64(msg)
                    msg.add_header('Content-Disposition', 'attachment', 
                                 filename=os.path.basename(file_path))
                    message.attach(msg)

            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the email
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            return f"Email sent successfully! Message ID: {sent_message['id']}"

        except Exception as e:
            return f"Error sending email: {str(e)}"

if __name__ == "__main__":
    tool = SendEmail()
    print(tool.forward(
        to="alex.candela@outlook.com",
        subject="Test Email",
        body="This is a test email sent using the SendEmail tool.",
    )) 