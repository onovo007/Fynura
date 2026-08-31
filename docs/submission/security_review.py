"""Read-only tracked/unignored-text credential-pattern check; no values printed."""
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
names = subprocess.check_output(["git", "-c", f"safe.directory={root.as_posix()}", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root).decode().split("\0")
patterns = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "github_token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "service_account_key": re.compile(r'"private_key"\s*:\s*"-----BEGIN'),
}
findings = []
large = []
for name in names:
    path = root/name
    if not name or not path.is_file():
        continue
    if path.stat().st_size > 10*1024*1024:
        large.append({"path": name, "bytes": path.stat().st_size})
    if path.suffix.lower() not in {".py", ".js", ".json", ".md", ".txt", ".html", ".yml", ".yaml", ".toml", ".ps1", ".example"}:
        continue
    for number,line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(),1):
        for kind,pattern in patterns.items():
            if pattern.search(line):
                findings.append({"path": name, "line": number, "kind": kind})
print(json.dumps({"tracked_and_unignored_paths": len([n for n in names if n]), "credential_pattern_findings": findings, "files_over_10MiB": large}))
