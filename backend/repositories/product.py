from datetime import UTC, datetime

from google.cloud import firestore

from backend.config import get_settings


class ProductRepository:
    def __init__(self, memory_repository):
        self.memory = memory_repository
        self._db = None
        self.sessions = {}

    def save_session(self, session):
        if self.durable:
            self.db().collection("product_sessions").document(session["session_id"]).set(session)
        self.sessions[session["session_id"]] = dict(session)

    def get_session(self, session_id):
        if self.durable:
            row = self.db().collection("product_sessions").document(session_id).get()
            return row.to_dict() if row.exists else None
        return self.sessions.get(session_id)

    def list_sessions(self, limit=5000):
        if self.durable:
            return [d.to_dict() for d in self.db().collection("product_sessions").order_by("started_at", direction=firestore.Query.DESCENDING).limit(limit).stream()]
        return sorted(self.sessions.values(), key=lambda s: s["started_at"], reverse=True)[:limit]

    @property
    def durable(self) -> bool:
        return get_settings().fynura_use_firestore

    def db(self):
        if self._db is None:
            self._db = firestore.Client(project=get_settings().google_cloud_project)
        return self._db

    def save_user(self, user: dict) -> dict:
        if self.durable:
            self.db().collection("users").document(user["user_id"]).set(user, merge=True)
        self.memory.users[user["user_id"]] = user
        return user

    def get_user(self, user_id: str) -> dict | None:
        if self.durable:
            snapshot = self.db().collection("users").document(user_id).get()
            return snapshot.to_dict() if snapshot.exists else None
        return self.memory.users.get(user_id)

    def list_users(self, limit: int = 100) -> list[dict]:
        if self.durable:
            return [doc.to_dict() for doc in self.db().collection("users").limit(limit).stream()]
        return list(self.memory.users.values())[:limit]

    def save_event(self, event: dict) -> None:
        if self.durable:
            self.db().collection("events").document(event["event_id"]).set(event)
        self.memory.events.append(event)

    def list_events(self, limit: int = 5000) -> list[dict]:
        if self.durable:
            return [doc.to_dict() for doc in self.db().collection("events").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()]
        return self.memory.events[-limit:]

    def set_account_status(self, user_id: str, status: str) -> dict | None:
        user = self.get_user(user_id)
        if not user:
            return None
        user.update({"account_status": status, "updated_at": datetime.now(UTC).isoformat()})
        return self.save_user(user)

    def delete_user(self, user_id: str) -> bool:
        found = self.get_user(user_id)
        if not found:
            return False
        if self.durable:
            self.db().collection("users").document(user_id).delete()
        self.memory.users.pop(user_id, None)
        return True
