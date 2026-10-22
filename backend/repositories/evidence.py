"""Shared immutable evidence snapshots with an atomic latest pointer."""
import json

from google.cloud import firestore

from backend.config import get_settings
from backend.models.domain import Assessment
from backend.models.source_document import SourceDocument
from backend.repositories.memory import MemoryRepository


class EvidenceRepository(MemoryRepository):
    def __init__(self):
        super().__init__()
        self._db = None

    def db(self):
        if self._db is None:
            self._db = firestore.Client(project=get_settings().google_cloud_project)
        return self._db

    def save_assessment(self, item):
        if get_settings().fynura_use_firestore:
            # JSON chunks avoid Firestore's 1 MiB document limit on global data.
            payload = item.model_dump_json()
            chunks = [payload[i:i + 100000] for i in range(0, len(payload), 100000)]
            ref = self.db().collection('evidence_snapshots').document(item.assessment_id)
            for index, chunk in enumerate(chunks):
                ref.collection('chunks').document(str(index)).set({'payload': chunk})
            batch = self.db().batch()
            batch.set(ref, {'chunks': len(chunks), 'threat_id': item.threat_id})
            from backend.services.analytics import intelligence_snapshot
            analytics = intelligence_snapshot(item)
            if analytics:
                batch.set(ref.collection('analysis').document('epidemiology'),
                          json.loads(json.dumps(analytics, default=str)))
            batch.set(self.db().collection('latest_evidence').document(item.threat_id),
                      {'assessment_id': item.assessment_id})
            batch.commit()
        return super().save_assessment(item)

    def get_assessment(self, assessment_id):
        cached = super().get_assessment(assessment_id)
        if cached or not get_settings().fynura_use_firestore:
            return cached
        ref = self.db().collection('evidence_snapshots').document(assessment_id)
        metadata = ref.get()
        if not metadata.exists:
            return None
        payload = ''.join(ref.collection('chunks').document(str(i)).get().to_dict()['payload']
                          for i in range(metadata.to_dict()['chunks']))
        item = Assessment.model_validate(json.loads(payload))
        self.assessments[item.assessment_id] = item
        return item

    def latest_assessment(self, threat_id):
        if get_settings().fynura_use_firestore:
            pointer = self.db().collection('latest_evidence').document(threat_id).get()
            if pointer.exists:
                return self.get_assessment(pointer.to_dict()['assessment_id'])
        return super().latest_assessment(threat_id)

    def save_source_document(self, document: SourceDocument) -> SourceDocument:
        if get_settings().fynura_use_firestore:
            # The checksum is an idempotency key. Only metadata is retained;
            # the publisher's PDF body is not copied into Firestore.
            self.db().collection('source_documents').document(document.checksum).set(
                document.model_dump(mode='json'), merge=True
            )
        return super().save_source_document(document)

    def get_source_document(self, checksum: str):
        cached = super().get_source_document(checksum)
        if cached or not get_settings().fynura_use_firestore:
            return cached
        snapshot = self.db().collection('source_documents').document(checksum).get()
        if not snapshot.exists:
            return None
        payload = snapshot.to_dict()
        self.source_documents[checksum] = payload
        return payload

    def has_source_document(self, checksum: str) -> bool:
        if super().has_source_document(checksum):
            return True
        if not get_settings().fynura_use_firestore:
            return False
        return self.db().collection('source_documents').document(checksum).get().exists
