"""Run with python -m scripts.backfill_measles_history. No cloud writes."""
import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from backend.sources.measles_history import eligibility_report, extract_history
from backend.sources.who_measles import URL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, default=Path("tmp/measles-history"))
    parser.add_argument("--input", type=Path, help="Replay a previously downloaded WHO workbook")
    parser.add_argument("--previous", type=Path, help="Previous normalized snapshot for revisions")
    args = parser.parse_args()
    if args.input:
        content = args.input.read_bytes()
    else:
        response = httpx.get(URL, timeout=60, follow_redirects=True,
                             headers={"User-Agent": "Fynura historical surveillance backfill/1.0"})
        response.raise_for_status()
        content = response.content
    now = datetime.now(UTC)
    snapshot = extract_history(content, now.isoformat())
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    report = eligibility_report(snapshot, now.date(), previous)
    output = args.output_directory.resolve()
    archive = output / "snapshots" / snapshot["sha256"]
    archive.mkdir(parents=True, exist_ok=True)
    raw = archive / "source.xlsx"
    if raw.exists():
        if hashlib.sha256(raw.read_bytes()).hexdigest() != snapshot["sha256"]:
            raise ValueError("Existing archive checksum mismatch")
    else:
        raw.write_bytes(content)
    normalized = archive / "normalized.json"
    if not normalized.exists():
        normalized.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    run = output / now.strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(exist_ok=False)
    (run / "eligibility.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    fields = ["iso3", "country", "first_period", "last_valid_period",
              "valid_months_through_cutoff", "complete_run_ending_at_cutoff",
              "recent_reported_months", "data_screening", "cusum_eligibility",
              "forecast_eligibility", "revision_comparison"]
    with (run / "countries.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in report["countries"]:
            writer.writerow({k: ("'" + str(row[k]) if str(row[k]).startswith(("=", "+", "-", "@")) else row[k]) for k in fields})
    candidates = [r for r in report["countries"] if r["data_screening"].startswith("CANDIDATE")]
    lines = ["# WHO measles historical eligibility report", "",
        f"Retrieved: {now.isoformat()}", f"Source: {URL}",
        f"SHA-256: `{snapshot['sha256']}`", "",
        f"Countries screened: {len(report['countries'])}",
        f"Reference month: {report['reference_cutoff']}",
        f"Countries passing the 60-month data screen: {len(candidates)}", "",
        "This is a data-readiness screen, not model validation. Live CUSUM and forecasting remain disabled.",
        "Missing values are never imputed. No countries are summed. Candidate status does not establish stable reporting practices.",
        "Historical revision comparison is unavailable without a previous snapshot; prospective snapshots preserve future revisions.",
        "", "## Country results", "",
        "| Country | ISO3 | Valid months | Complete months ending at cutoff | Recent 60 months | Data screen |",
        "|---|---|---:|---:|---:|---|"]
    for row in report["countries"]:
        lines.append(f"| {row['country'].replace('|', '/')} | {row['iso3']} | {row['valid_months_through_cutoff']} | {row['complete_run_ending_at_cutoff']} | {row['recent_reported_months']} | {row['data_screening']} |")
    (run / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(run / "REPORT.md"), "csv": str(run / "countries.csv"),
        "normalized_snapshot": str(normalized), "sha256": snapshot["sha256"],
        "countries": len(report["countries"]), "reference_cutoff": report["reference_cutoff"],
        "candidates": len(candidates), "rejected_rows": len(snapshot["rejected_source_rows"]),
        "examples": [{k: r[k] for k in ("iso3", "country", "recent_reported_months", "complete_run_ending_at_cutoff")} for r in candidates[:10]]}, indent=2))


if __name__ == "__main__":
    main()
