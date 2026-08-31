"""Read-only historical evidence API and bounded, deterministic historical answers."""
import gzip
import json
import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from backend.models.domain import AskResponse


@lru_cache(maxsize=1)
def catalog():
    path = Path(__file__).resolve().parents[2] / "data/history/catalog.json.gz"
    result = json.loads(gzip.decompress(path.read_bytes()))
    extra = path.with_name('owid.json.gz')
    if extra.exists():
        result['datasets'].update(json.loads(gzip.decompress(extra.read_bytes()))['datasets'])
    return result


def series_summary(points, frequency, start, end):
    valid = [p for p in points if p['value'] is not None]
    if frequency == 'outbreak':
        return {'total': None, 'label': 'Separate outbreak totals', 'note': 'Separate outbreaks may overlap geographically and have different case definitions. No cross-outbreak sum.', 'count': len(valid)}
    expected = (end - start + 1) * (12 if frequency == 'monthly' else 1)
    unique = len({p['period'] for p in valid}) == len(valid)
    complete = unique and len(valid) == expected
    total = sum(p['value'] for p in valid) if valid and unique else None
    peak = max(valid, key=lambda p: p['value']) if valid else None
    return {'total': total, 'label': 'Reported cases in selected period' if complete else 'Reported cases in available periods (partial)',
        'complete': complete, 'count': len(valid), 'expected': expected, 'missing': max(0, expected-len(valid)),
        'first': valid[0]['period'] if valid else None, 'last': valid[-1]['period'] if valid else None,
        'peak': peak, 'evidence_ids': [p['evidence_id'] for p in valid],
        'note': 'Sum of non-overlapping reports in this dataset, not a single outbreak total. Missing periods are not zero; changing surveillance and under-reporting limit comparability.'}


def history_metadata():
    return {key: {**{k: v for k, v in item.items() if k not in {"countries", "skipped_entries", "original_metadata"}},
        "countries": [{"code": c["code"], "name": c["name"]} for c in item["countries"]],
        "first": min(p["period"] for c in item["countries"] for p in c["points"]),
        "last": max(p["period"] for c in item["countries"] for p in c["points"])}
        for key, item in catalog()["datasets"].items()}


def historical_series(threat, country, start=2010, end=2026):
    item = catalog()["datasets"].get(threat)
    if not item or not 1900 <= start <= end <= 2100:
        raise ValueError("Invalid historical selection")
    chosen = next((c for c in item["countries"] if c["code"] == country), None)
    if not chosen:
        raise ValueError("Country is not available in this archive")
    points = [p for p in chosen["points"] if start <= int(p["period"][:4]) <= end]
    return {**{k: v for k, v in item.items() if k not in {"countries", "skipped_entries", "original_metadata"}},
        "threat": threat, "country": country, "geography": chosen["name"],
        "start": start, "end": end, "points": points,
        "summary": series_summary(points, item['frequency'], start, end),
        "empty_message": "No verified historical observation for this selection. Missing data are not zero."}


def historical_answer(request):
    q = request.question.lower()
    context = request.context
    in_explorer = context and context.visual == "historical_archive"
    years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", q)]
    total_request = any(w in q for w in ('total', 'since the start', 'inception', 'year to date'))
    is_measles = 'measles' in q or request.threat_id == 'measles' or (context and context.threat_id == 'measles')
    if not in_explorer and not years and not any(w in q for w in ("historical", "past outbreak", "history of", "annual", "owid", "our world in data")) and not (total_request and is_measles):
        return None
    explicit = next((t for t in ("measles", "cholera", "ebola") if t in q), None)
    threat = explicit or request.threat_id or (context.threat_id if context else None)
    if threat not in catalog()["datasets"]:
        return AskResponse(answer="Choose a disease and country in Historical evidence to ask about past reports.", evidence_ids=[], declined=True)
    options = catalog()["datasets"][threat]["countries"]
    aliases = {"usa": "USA", "united states": "USA", "us ": "USA", "uk": "GBR"}
    country = next((c["code"] for c in sorted(options, key=lambda c: len(c['name']), reverse=True) if re.search(r"\b"+re.escape(c["name"].lower())+r"\b", q) or re.search(r"\b"+re.escape(c["code"].lower())+r"\b", q)), None)
    country = country or next((code for name, code in aliases.items() if re.search(r"\b"+re.escape(name.strip())+r"\b", q) and any(c["code"] == code for c in options)), None)
    if not country and context and context.geography:
        country = next((c['code'] for c in options if c['name'].lower() == context.geography.lower()), None)
    scope = (context.visual_context or {}) if in_explorer and (not explicit or explicit == context.threat_id) else {}
    country = country or scope.get("country") or ("ALL" if threat == "ebola" else None)
    if not country:
        return AskResponse(answer=f"Historical {threat} data are available by country. Select a country in Historical evidence; I will not invent a global total.", evidence_ids=[], declined=True)
    dataset = scope.get('dataset', threat)
    if dataset not in catalog()['datasets'] or catalog()['datasets'][dataset].get('disease', dataset) != threat:
        dataset = threat
    if ('annual' in q or 'our world in data' in q or 'owid' in q) and threat + '_annual' in catalog()['datasets']:
        dataset = threat + '_annual'
    start, end = (min(years), max(years)) if years else (scope.get("start", 2010), scope.get("end", 2026))
    if total_request and not years and not in_explorer:
        start = end = datetime.now(UTC).year
    try:
        data = historical_series(dataset, country, int(start), int(end))
    except (ValueError, TypeError):
        return AskResponse(answer="That historical selection is unavailable. Choose a listed country and year range.", evidence_ids=[], declined=True)
    points = [p for p in data["points"] if p["value"] is not None]
    if not points:
        return AskResponse(answer=data["empty_message"], evidence_ids=[], declined=True)
    chosen = points[:8] if threat == "ebola" else [points[0], points[-1]] if len(points) > 1 else points
    facts = [f"{p.get('label', p['period'])}: {p['value']:,.0f} {data['unit']}" for p in chosen]
    answer = f"Historical {threat} evidence for {data['geography']} ({start} to {end}). " + "; ".join(facts) + ". "
    if threat != "ebola":
        summary = data['summary']
        answer += f"{summary['label']}: {summary['total']:,.0f} across {summary['count']} {data['frequency']} reports, covering {summary['first']} to {summary['last']}. "
        answer += f"{summary['missing']} periods in the requested range lack reports. " if summary['missing'] else "All requested reporting periods are represented. "
        answer += summary['note'] + ' '
        peak = summary['peak']
        answer += f"Peak reported period: {peak['period']} with {peak['value']:,.0f} cases. "
        chosen = points
    if "compar" in q or "current" in q or "today" in q:
        answer += "Compare current evidence separately: the archive and current reports may differ in period, geography and case definition; no direct growth estimate is justified here. "
    return AskResponse(answer=answer, evidence_ids=[p["evidence_id"] for p in chosen],
        subject={"label": "HISTORICAL EVIDENCE", "geography": data["geography"]},
        limitations=[data["limitations"], "Bounded archive retrieval, not unrestricted live web research. Open the history table for all observations."],
        sources=[{"organization": data["source"], "title": data["title"], "url": data["source_url"], "reporting_cutoff": points[-1]['period'], "retrieved_at": data["retrieved_at"], "historical": True}])
