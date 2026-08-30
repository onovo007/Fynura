"""Opaque browser-session access, bound to the Firebase cookie, with durable revocation."""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import pycountry


def countries():
    return sorted([{"country_name": c.name, "iso2": c.alpha_2, "iso3": c.alpha_3}
                   for c in pycountry.countries], key=lambda c: c["country_name"])


def country_record(value):
    aliases = {"United States": "US", "United Kingdom": "GB",
               "Democratic Republic of the Congo": "CD"}
    try:
        c = pycountry.countries.lookup(aliases.get(value, value))
        return {"country_name": c.name, "iso2": c.alpha_2, "iso3": c.alpha_3}
    except LookupError:
        raise ValueError("Select a country from the standardized list") from None


def cookie_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def active_session(request, repository):
    sid = request.cookies.get("fynura_access", "")
    if len(sid) != 64 or any(c not in "0123456789abcdef" for c in sid):
        return None
    record = repository.get_session(sid)
    if not record or record.get("ended_at") or datetime.fromisoformat(record["expires_at"]) <= datetime.now(UTC):
        return None
    if not secrets.compare_digest(record["cookie_digest"], cookie_digest(request.cookies.get("fynura_session", ""))):
        return None
    user = repository.get_user(record["user_id"])
    return record if user and user.get("account_status") == "active" else None


def start_session(request, repository, user):
    existing = active_session(request, repository)
    if existing and existing["user_id"] == user["user_id"]:
        return existing
    now = datetime.now(UTC)
    row = {"session_id": secrets.token_hex(32), "user_id": user["user_id"],
           "country": user["country"], "iso2": user["iso2"], "iso3": user["iso3"],
           "stakeholder_role": user.get("stakeholder_role"),
           "started_at": now.isoformat(), "last_active_at": now.isoformat(),
           "expires_at": (now + timedelta(hours=8)).isoformat(), "ended_at": None,
           "cookie_digest": cookie_digest(request.cookies.get("fynura_session", ""))}
    repository.save_session(row)
    return row


def end_session(request, repository):
    row = active_session(request, repository)
    if row:
        row["ended_at"] = datetime.now(UTC).isoformat()
        repository.save_session(row)
