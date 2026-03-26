import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain.tools import tool
from googleapiclient.discovery import build
from backend.tools.google_auth import get_google_credentials

@tool
def draft_email(to: str, subject: str, body: str) -> str:
    """Draft an email via Gmail.
    Use this when the teacher wants to write an email
    to students, parents or colleagues.
    Always draft first — never send without confirmation."""
    try:
        creds = get_google_credentials()
        service = build("gmail", "v1", credentials=creds)

        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw}}
        ).execute()

        return f"Email drafted ✓ Draft ID: {draft['id']} | Subject: '{subject}' | To: {to}"
    except Exception as e:
        return f"Email drafting failed: {str(e)}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail.
    Only use this when the teacher explicitly confirms
    they want to send the email immediately."""
    try:
        creds = get_google_credentials()
        service = build("gmail", "v1", credentials=creds)

        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return f"Email sent ✓ Message ID: {sent['id']} | Subject: '{subject}' | To: {to}"
    except Exception as e:
        return f"Email sending failed: {str(e)}"