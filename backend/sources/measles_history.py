"""Versioned WHO monthly history, kept separate from current dashboard totals."""
import hashlib
import io
from collections import Counter, defaultdict
from datetime import date
from math import isfinite

import openpyxl

from backend.sources.who_measles import PORTAL, URL

VERSION = "who-measles-history-1.0"


def month_index(period):
    year, month = map(int, period.split("-"))
    date(year, month, 1)
    return year * 12 + month - 1


def month_label(index):
    year, month = divmod(index, 12)
    return f"{year:04d}-{month + 1:02d}"


def extract_history(content, retrieved_at):
    digest = hashlib.sha256(content).hexdigest()
    book = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        iterator = book["WEB"].iter_rows(values_only=True)
        header = [" ".join(str(x or "").split()).lower() for x in next(iterator)]
        required = {"region", "country", "iso3", "year", "month", "measles total"}
        if not required.issubset(header):
            raise ValueError("WHO workbook schema changed; refusing positional interpretation")
        positions = {name: header.index(name) for name in required}
        groups = defaultdict(list)
        rejected = []
        for number, row in enumerate(iterator, 2):
            if not any(x is not None for x in row):
                continue
            get = lambda name, row=row: row[positions[name]]
            try:
                iso3 = str(get("iso3") or "").strip().upper()
                if len(iso3) != 3 or not iso3.isalpha():
                    raise ValueError("Invalid country code")
                period = date(int(get("year")), int(get("month")), 1).strftime("%Y-%m")
            except (ValueError, TypeError):
                rejected.append(number)
                continue
            raw = get("measles total")
            status = "reported"
            try:
                value = float(raw)
                if not isfinite(value) or value < 0 or not value.is_integer():
                    raise ValueError("Not a nonnegative count")
                value = int(value)
            except (ValueError, TypeError):
                value = None
                status = "missing" if raw is None or str(raw).strip() == "" else "invalid"
            groups[iso3, period].append({"country": str(get("country")),
                "region": str(get("region")), "value": value, "status": status,
                "source_row": number})
    finally:
        book.close()
    countries = defaultdict(list)
    for (iso3, period), candidates in sorted(groups.items()):
        identities = {(r["country"], r["region"], r["value"], r["status"]) for r in candidates}
        status = candidates[0]["status"] if len(identities) == 1 else "conflict"
        countries[iso3].append({"period": period, "country": candidates[0]["country"],
            "region": candidates[0]["region"],
            "value": candidates[0]["value"] if status == "reported" else None,
            "status": status, "source_rows": [r["source_row"] for r in candidates],
            "duplicate_rows": len(candidates) - 1,
            "evidence_id": f"{digest}:{iso3}:{period}"})
    return {"version": VERSION, "sha256": digest, "retrieved_at": retrieved_at,
        "source_url": URL, "source_portal": PORTAL, "publication_date": None,
        "indicator": "reported_measles_cases", "unit": "cases", "frequency": "monthly",
        "case_definition": "WHO provisional measles total by final classification",
        "period_semantics": "monthly reported total, not cumulative",
        "rejected_source_rows": rejected, "countries": dict(countries)}


def eligibility_report(snapshot, as_of, previous=None, coverage_floor=120, window=60):
    """Data-screening candidates are NOT validated CUSUM/forecast eligibility."""
    if window < 25 or coverage_floor < 1:
        raise ValueError("Invalid screening configuration")
    current_month = as_of.year * 12 + as_of.month - 1
    coverage = Counter(p["period"] for rows in snapshot["countries"].values()
                       for p in rows if p["status"] == "reported"
                       and month_index(p["period"]) < current_month)
    candidates = [p for p, n in coverage.items() if n >= coverage_floor]
    if not candidates:
        raise ValueError("No completed reference month meets coverage floor")
    cutoff = max(candidates)
    end = month_index(cutoff)
    recent = [month_label(i) for i in range(end - window + 1, end + 1)]
    reports = []
    old_countries = (previous or {}).get("countries", {})
    for iso3, rows in sorted(snapshot["countries"].items()):
        by_period = {p["period"]: p for p in rows}
        usable = {p["period"] for p in rows if p["status"] == "reported"
                  and p["period"] <= cutoff}
        absent = [p for p in recent if p not in by_period]
        bad = [p for p in recent if p in by_period and p not in usable]
        tail = 0
        while month_label(end - tail) in usable:
            tail += 1
        longest = run = 0
        prior_index = None
        for period in sorted(usable):
            index = month_index(period)
            run = run + 1 if prior_index == index - 1 else 1
            longest = max(longest, run)
            prior_index = index
        old = {p["period"]: p for p in old_countries.get(iso3, [])}
        revisions = [{"period": p, "previous": old[p]["value"], "current": row["value"]}
                     for p, row in by_period.items() if p in old and
                     (old[p]["value"], old[p]["status"]) != (row["value"], row["status"])]
        removed = sorted(set(old) - set(by_period))
        variation = len({by_period[p]["value"] for p in recent if p in usable}) > 1
        identity_stable = len({(by_period[p]["country"], by_period[p]["region"])
                               for p in recent if p in by_period}) == 1
        reasons = []
        if absent or bad:
            reasons.append("Incomplete recent monthly history")
        if not variation:
            reasons.append("No usable variation in recent history")
        if not identity_stable:
            reasons.append("Country or region labels changed; review required")
        if any(r["period"] in recent for r in revisions) or set(removed).intersection(recent):
            reasons.append("Recent history revised or removed since previous snapshot")
        if snapshot["rejected_source_rows"]:
            reasons.append("Unassigned invalid source rows require workbook review")
        if current_month - end > 3:
            reasons.append("Reference month is more than three months behind retrieval")
        data_candidate = not reasons
        reports.append({"iso3": iso3, "country": rows[-1]["country"],
            "first_period": rows[0]["period"], "last_source_period": rows[-1]["period"],
            "last_valid_period": max(usable) if usable else None,
            "valid_months_through_cutoff": len(usable), "longest_complete_run": longest,
            "complete_run_ending_at_cutoff": tail, "recent_window_months": window,
            "recent_reported_months": window - len(absent) - len(bad),
            "missing_periods": absent, "invalid_or_missing_value_periods": bad,
            "duplicate_rows": sum(p["duplicate_rows"] for p in rows),
            "conflicting_periods": [p["period"] for p in rows if p["status"] == "conflict"],
            "revision_comparison": "compared" if iso3 in old_countries else "unavailable",
            "revisions": revisions, "removed_periods": removed,
            "data_screening": "CANDIDATE FOR METHOD VALIDATION" if data_candidate else "NOT READY",
            "cusum_eligibility": "LIMITED" if data_candidate else "NOT ELIGIBLE",
            "forecast_eligibility": "NOT VALIDATED", "signal": "WITHHELD",
            "reasons": reasons + ["Seasonal/count baseline and thresholds not validated",
                "Historical reporting-definition stability requires source review",
                "A current workbook is not a historical as-published archive"]})
    return {"version": VERSION, "snapshot_sha256": snapshot["sha256"],
        "retrieved_at": snapshot["retrieved_at"], "source_url": snapshot["source_url"],
        "reference_cutoff": cutoff, "reference_coverage_countries": coverage[cutoff],
        "screening_window": window, "rules": f"{window} months is a screening target, not a validated statistical minimum. No imputation or cross-country summation.",
        "countries": reports, "candidate_count": sum(r["data_screening"].startswith("CANDIDATE") for r in reports),
        "live_cusum_enabled": False, "forecast_enabled": False}
