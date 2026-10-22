from backend.models.domain import Assessment, Watch


class MemoryRepository:
    def __init__(self):
        self.assessments: dict[str, Assessment] = {}
        self.watches: dict[str, Watch] = {}
        self.users: dict[str, dict] = {}
        self.events: list[dict] = []
        self.source_documents: dict[str, dict] = {}

    def save_assessment(self, item: Assessment) -> Assessment:
        self.assessments[item.assessment_id] = item
        return item

    def latest_assessment(self, threat_id: str) -> Assessment | None:
        items = [x for x in self.assessments.values() if x.threat_id == threat_id]
        return max(items, key=lambda x: x.generated_at) if items else None

    def get_assessment(self, assessment_id: str) -> Assessment | None:
        return self.assessments.get(assessment_id)

    def save_watch(self, watch: Watch) -> Watch:
        self.watches[watch.watch_id] = watch
        return watch

    def save_source_document(self, document):
        payload = document.model_dump(mode="json")
        self.source_documents[document.checksum] = payload
        return document

    def get_source_document(self, checksum: str):
        return self.source_documents.get(checksum)

    def has_source_document(self, checksum: str) -> bool:
        return checksum in self.source_documents
