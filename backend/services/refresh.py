"""Bounded scheduled refresh. Keep last successful evidence on source failure."""
import asyncio
import logging
from datetime import UTC, datetime, timedelta

from google.cloud import firestore

from backend.config import get_settings

CADENCE_HOURS = {'ebola': 12, 'cholera': 24, 'measles': 24}


class RefreshService:
    def __init__(self, repository, pipeline):
        self.repo, self.pipeline = repository, pipeline
        self.statuses = {}

    def status(self, threat):
        if get_settings().fynura_use_firestore:
            doc = self.repo.db().collection('refresh_status').document(threat).get()
            return doc.to_dict() or {}
        return self.statuses.get(threat, {})

    def claim(self, threat, now):
        def due(status):
            return all(not status.get(k) or datetime.fromisoformat(status[k]) <= now
                       for k in ('next_scheduled_check', 'lease_until'))
        lease = (now + timedelta(minutes=10)).isoformat()
        if get_settings().fynura_use_firestore:
            ref = self.repo.db().collection('refresh_status').document(threat)

            @firestore.transactional
            def claim_in_transaction(transaction):
                status = ref.get(transaction=transaction).to_dict() or {}
                if not due(status):
                    return False
                transaction.set(ref, {'lease_until': lease}, merge=True)
                return True
            return claim_in_transaction(self.repo.db().transaction())
        status = self.status(threat)
        if not due(status):
            return False
        self.statuses[threat] = {**status, 'lease_until': lease}
        return True

    async def refresh(self, threat):
        now = datetime.now(UTC)
        if not self.claim(threat, now):
            return self.repo.latest_assessment(threat)
        status = self.status(threat)
        try:
            item = await getattr(self.pipeline, f'assess_{threat}')()
            status.update({
                'state': 'verified_snapshot',
                'last_successful_retrieval': item.evidence_cutoff.isoformat(),
                'last_verification': item.generated_at.isoformat(),
                'last_source_publication': max((str(o.publication_date) for o in item.observations if o.publication_date), default=None),
                'latest_reporting_cutoff': max((str(o.reporting_period_end) for o in item.observations if o.reporting_period_end), default=None),
            })
        except Exception:
            logging.getLogger('fynura.refresh').exception('Source refresh failed: %s', threat)
            item = self.repo.latest_assessment(threat)
            status['state'] = 'cached_snapshot' if item else 'unavailable'
        status.update({'last_check': now.isoformat(), 'lease_until': None,
                       'next_scheduled_check': (now + timedelta(hours=CADENCE_HOURS[threat])).isoformat()})
        if get_settings().fynura_use_firestore:
            self.repo.db().collection('refresh_status').document(threat).set(status)
        self.statuses[threat] = status
        return item

    async def run(self):
        return await asyncio.gather(*(self.refresh(t) for t in CADENCE_HOURS))
