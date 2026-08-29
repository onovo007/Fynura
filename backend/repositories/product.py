from datetime import UTC, datetime

from google.cloud import firestore

from backend.config import get_settings


class ProductRepository:
    def __init__(self, memory_repository):
        self.memory = memory_repository
        self._db = None

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
            return [doc.to_dict() for doc in self.db().collection("events").limit(limit).stream()]
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
