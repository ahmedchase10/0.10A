import secrets
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, Response, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from backend.server.db.engine import get_session
from backend.server.auth.jwt import verify_token  # 🔑 Your exact JWT verifier
from backend.google.gmail import (
CLIENT_CONFIG,SCOPES,REDIRECT_URI,
    get_valid_credentials,
    save_credentials,
    send_gmail,
    unlink_gmail
)

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    token: str  # ✅ JWT passed in request body

class UnlinkRequest(BaseModel):
    token: str  # ✅ JWT in body, consistent with your other endpoints


router = APIRouter(prefix="/gmail", tags=["Gmail Integration"])

def verify_teacher_token(token: str) -> Dict[str, Any]:
    """Wrapper around your verify_token to standardize error handling in routes."""
    try:
        return verify_token(token)
    except Exception as e:
        # Swap to AppError if your global exception handler requires it
        raise HTTPException(401, f"Invalid or expired token: {str(e)}")


# 🔐 STEP 1: Redirect to Google Consent
@router.get("/auth/google/login")
def google_login(
        request: Request,
        token: str = Query(...),
        session: Session = Depends(get_session)
):
    teacher = verify_teacher_token(token)
    teacher_id = teacher["id"]
    email = teacher["email"]

    if get_valid_credentials(session, teacher_id, email):
        return RedirectResponse(url="http://localhost:3000/?gmail_connected=true", status_code=302)

    nonce = secrets.token_urlsafe(16)
    state = f"{teacher_id}|{email}|{nonce}"

    # Create flow & generate auth URL (auto-generates PKCE code_verifier)
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent", state=state)

    # 🔑 Extract the verifier Google now requires
    code_verifier = flow.code_verifier

    redirect_response = RedirectResponse(url=auth_url, status_code=302)
    redirect_response.set_cookie(key="oauth_state", value=state, httponly=True, secure=False, samesite="lax",
                                 max_age=600, path="/")
    redirect_response.set_cookie(key="oauth_code_verifier", value=code_verifier, httponly=True, secure=False,
                                 samesite="lax", max_age=600, path="/")
    return redirect_response
# 🔁 STEP 2: Google Callback
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

# 📤 STEP 3: Send Email (JWT in Body)
@router.post("/send-email")
def send_email_endpoint(
    payload: SendEmailRequest,
    session: Session = Depends(get_session)
):
    # ✅ Extract & verify JWT from request body
    teacher = verify_teacher_token(payload.token)
    teacher_id = teacher["id"]
    email = teacher["email"]

    creds = get_valid_credentials(session, teacher_id, email)
    if not creds:
        raise HTTPException(401, "Gmail not connected or token expired. Please reconnect.")

    try:
        result = send_gmail(creds, payload.to, payload.subject, payload.body)
        return {"message": "Email sent", "gmail_message_id": result.get("id")}
    except Exception as e:
        raise HTTPException(500, f"Failed to send email: {str(e)}")

@router.post("/unlink")
def unlink_gmail_endpoint(
    payload: UnlinkRequest,
    session: Session = Depends(get_session)
):
    # 1️⃣ Verify JWT & extract teacher context
    teacher = verify_teacher_token(payload.token)
    teacher_id = teacher["id"]
    email = teacher["email"]

    # 2️⃣ Call business logic
    result = unlink_gmail(session, teacher_id, email)

    # 3️⃣ Return appropriate response
    if not result["success"]:
        raise HTTPException(404, result["message"])

    return {"message": result["message"]}