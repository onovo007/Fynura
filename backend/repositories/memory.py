from backend.models.domain import Assessment, Watch


class MemoryRepository:
    def __init__(self):
        self.assessments: dict[str, Assessment] = {}
        self.watches: dict[str, Watch] = {}

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
