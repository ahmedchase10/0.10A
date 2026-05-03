import os
import base64
from typing import Optional
from email.message import EmailMessage

import requests
from cryptography.fernet import Fernet
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlmodel import Session, select

# Import your models
from backend.server.db.dbModels import Teacher, UserEmailCredentials

# ─── ENV CONFIG ───────────────────────────────────────────────────────────────
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/gmail/auth/google/callback")
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
FERNET_KEY = os.getenv("FERNET_KEY")

if not all([CLIENT_ID, CLIENT_SECRET, FERNET_KEY]):
    raise ValueError("Missing env vars: ClientID, ClientSecret, FERNET_KEY")

fernet = Fernet(FERNET_KEY.encode())

CLIENT_CONFIG = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}


# ─── ENCRYPTION HELPERS ───────────────────────────────────────────────────────
def encrypt_token(token: Optional[str]) -> Optional[str]:
    return fernet.encrypt(token.encode()).decode() if token else None


def decrypt_token(encrypted_token: Optional[str]) -> Optional[str]:
    return fernet.decrypt(encrypted_token.encode()).decode() if encrypted_token else None


# ─── DB OPERATIONS ────────────────────────────────────────────────────────────
def save_credentials(session: Session, teacher_id: int, email: str, creds: Credentials):
    """Upsert credentials for a specific teacher"""
    stmt = select(UserEmailCredentials).where(
        UserEmailCredentials.user_id == teacher_id,
        UserEmailCredentials.email == email
    )
    db_creds = session.exec(stmt).first()

    if db_creds:
        db_creds.access_token = encrypt_token(creds.token)
        db_creds.refresh_token = encrypt_token(creds.refresh_token)
        db_creds.token_expiry = creds.expiry
    else:
        db_creds = UserEmailCredentials(
            user_id=teacher_id,
            email=email,
            access_token=encrypt_token(creds.token),
            refresh_token=encrypt_token(creds.refresh_token),
            token_expiry=creds.expiry
        )
        session.add(db_creds)
    session.commit()



from datetime import timezone  # ✅ Ensure this is at the top of the file

def load_credentials(session: Session, teacher_id: int, email: str) -> Optional[Credentials]:
    """Load and reconstruct Google Credentials from DB"""
    stmt = select(UserEmailCredentials).where(
        UserEmailCredentials.user_id == teacher_id,
        UserEmailCredentials.email == email
    )
    db_creds = session.exec(stmt).first()

    if not db_creds or not db_creds.refresh_token:
        return None

    # 🔑 FORCE TIMEZONE AWARENESS (fixes TypeError on .expired/.valid checks)
    expiry = db_creds.token_expiry
    if expiry is not None and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    return Credentials(
        token=decrypt_token(db_creds.access_token),
        refresh_token=decrypt_token(db_creds.refresh_token),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES,
        expiry=expiry
    )


def get_valid_credentials(session: Session, teacher_id: int, email: str) -> Optional[Credentials]:
    """Get valid credentials, auto-refreshing if expired. Crash-safe."""
    creds = load_credentials(session, teacher_id, email)
    if not creds:
        return None

    # 🛡️ Wrap Google's datetime checks to prevent naive/aware TypeError
    try:
        if creds.valid:
            return creds
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(session, teacher_id, email, creds)
            return creds
    except TypeError:
        # Fallback: if timezone comparison fails, force a refresh
        if creds.refresh_token:
            try:
                creds.refresh(Request())
                save_credentials(session, teacher_id, email, creds)
                return creds
            except Exception as e:
                print(f"⚠️ Token refresh failed: {e}")
    return None


# ─── OAUTH FLOW HELPERS ───────────────────────────────────────────────────────
def get_authorization_url(state: str) -> str:
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    # ✅ Automatically injects response_type=code, preventing the 400 error
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state
    )
    return auth_url


def exchange_code_for_credentials(code: str) -> Credentials:
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    flow.fetch_token(code=code)
    return flow.credentials


# ─── EMAIL SENDING ────────────────────────────────────────────────────────────
def send_gmail(creds: Credentials, to: str, subject: str, body: str) -> dict:
    service = build("gmail", "v1", credentials=creds)
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()
#unlink Email
def unlink_gmail(session: Session, teacher_id: int, email: str) -> dict:
    """
    Remove stored credentials from DB and revoke access on Google's side.
    Returns {"success": bool, "message": str}
    """
    stmt = select(UserEmailCredentials).where(
        UserEmailCredentials.user_id == teacher_id,
        UserEmailCredentials.email == email
    )
    db_creds = session.exec(stmt).first()

    if not db_creds:
        return {"success": False, "message": "No Gmail account is currently connected."}

    # 🔑 Revoke on Google's side (best-effort, non-blocking)
    token_to_revoke = decrypt_token(db_creds.access_token) or decrypt_token(db_creds.refresh_token)
    if token_to_revoke:
        try:
            resp = requests.post(f"https://oauth2.googleapis.com/revoke?token={token_to_revoke}")
            if resp.status_code != 200:
                print(f"⚠️ Google revoke warning: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"⚠️ Failed to contact Google revoke endpoint: {e}")

    # 🗑️ Delete from DB
    session.delete(db_creds)
    session.commit()

    return {"success": True, "message": "Gmail account unlinked successfully. You can now connect a new one."}