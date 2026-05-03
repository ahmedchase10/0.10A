import os
import secrets
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, Response, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from backend.server.db.engine import get_session
from backend.server.auth.dependencies import require_auth
from backend.server.auth.jwt import verify_token  # Only for the redirect step
from backend.google.gmail import (
CLIENT_CONFIG,SCOPES,REDIRECT_URI,
    save_credentials,
    get_valid_credentials,
    send_gmail,
    unlink_gmail
)
router = APIRouter(prefix="/gmail", tags=["Gmail Integration"])


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str


# 🔐 STEP 1: OAuth Redirect (MUST use query param due to browser limitation)
@router.get("/auth/google/login")
def google_login(
        request: Request,
        response: Response,
        token: str = Query(...),
        session: Session = Depends(get_session)
):
    teacher = verify_token(token)  # Manual decode only for this redirect
    teacher_id = teacher["id"]
    email = teacher["email"]

    if get_valid_credentials(session, teacher_id, email):
        return RedirectResponse(url="http://localhost:3000/?gmail_connected=true", status_code=302)

    nonce = secrets.token_urlsafe(16)
    state = f"{teacher_id}|{email}|{nonce}"
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent", state=state)
    redirect_response = RedirectResponse(url=auth_url, status_code=302)
    redirect_response.set_cookie(key="oauth_state", value=state, httponly=True, secure=False, samesite="lax",
                                 max_age=600, path="/")
    redirect_response.set_cookie(key="oauth_code_verifier", value=flow.code_verifier, httponly=True, secure=False,
                                 samesite="lax", max_age=600, path="/")
    return redirect_response


# 🔁 STEP 2: Callback (Unchanged)
@router.get("/auth/google/callback")
def google_callback(
    request: Request,
    response: Response,
    session: Session = Depends(get_session)
):
    cookie_state = request.cookies.get("oauth_state")
    cookie_verifier = request.cookies.get("oauth_code_verifier")
    query_state = request.query_params.get("state")
    code = request.query_params.get("code")

    if not code or not cookie_state or cookie_state != query_state:
        raise HTTPException(400, "Invalid or expired OAuth state")

    response.delete_cookie("oauth_state")
    response.delete_cookie("oauth_code_verifier")

    try:
        teacher_id_str, email, _ = query_state.split("|")
        teacher_id = int(teacher_id_str)
    except ValueError:
        raise HTTPException(400, "Malformed state parameter")

    try:
        flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        # 🔑 Pass the stored verifier to satisfy Google's PKCE requirement
        flow.fetch_token(code=code, code_verifier=cookie_verifier)
        creds = flow.credentials
        save_credentials(session, teacher_id, email, creds)
    except Exception as e:
        raise HTTPException(400, f"Token exchange failed: {str(e)}")

    return RedirectResponse(url="http://localhost:3000/?gmail_connected=true", status_code=302)


# 📤 STEP 3: Send Email (Now uses require_auth + Authorization header)
@router.post("/send-email")
def send_email_endpoint(
        payload: SendEmailRequest,
        teacher: Dict[str, Any] = Depends(require_auth),
        session: Session = Depends(get_session)
):
    creds = get_valid_credentials(session, teacher["id"], teacher["email"])
    if not creds:
        raise HTTPException(401, "Gmail not connected or token expired. Please reconnect.")

    result = send_gmail(creds, payload.to, payload.subject, payload.body)
    return {"message": "Email sent", "gmail_message_id": result.get("id")}


# 🔓 STEP 4: Unlink (Now uses require_auth + Authorization header)
@router.post("/unlink")
def unlink_gmail_endpoint(
        teacher: Dict[str, Any] = Depends(require_auth),
        session: Session = Depends(get_session)
):
    result = unlink_gmail(session, teacher["id"], teacher["email"])
    if not result["success"]:
        raise HTTPException(404, result["message"])
    return {"message": result["message"]}