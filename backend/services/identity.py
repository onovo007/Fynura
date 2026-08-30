from datetime import timedelta

import firebase_admin
from fastapi import HTTPException, Request
from firebase_admin import auth

from backend.config import get_settings


def initialize_identity() -> None:
    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={"projectId": get_settings().google_cloud_project})


def verify_token(token: str, session: bool = False) -> dict:
    initialize_identity()
    try:
        if session:
            return auth.verify_session_cookie(token, check_revoked=True)
        return auth.verify_id_token(token, check_revoked=True)
    except Exception as exc:
        raise HTTPException(401, "Valid Fynura sign-in required") from exc


def optional_identity(request: Request) -> dict | None:
    session = request.cookies.get("fynura_session")
    if session:
        try:
            return verify_token(session, session=True)
        except HTTPException:
            return None
    authorization = request.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return verify_token(authorization.split(" ", 1)[1])
    return None


def require_identity(request: Request) -> dict:
    identity = optional_identity(request)
    if not identity:
        raise HTTPException(401, "Fynura sign-in required")
    return identity


def require_owner(request: Request) -> dict:
    owner = (get_settings().fynura_owner_email or "").lower()
    if not owner:
        raise HTTPException(403, "Owner authorization required")
    identity = require_identity(request)
    if identity.get("email", "").lower() != owner:
        raise HTTPException(403, "Owner authorization required")
    return identity


def create_session_cookie(id_token: str) -> str:
    initialize_identity()
    return auth.create_session_cookie(
        id_token, expires_in=timedelta(days=get_settings().fynura_session_days)
    )
