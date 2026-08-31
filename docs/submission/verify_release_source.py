"""Compare a Cloud Build source ZIP with local or committed runtime inputs.

Usage: python docs/submission/verify_release_source.py PATH_TO_ZIP [--git HEAD]
No archive extraction, credential access or network calls. Line endings are
normalized for text files because Git may store LF for a Windows checkout.
"""
import argparse
from pathlib import Path
import subprocess
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('archive')
parser.add_argument('--git', dest='revision')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]


def in_scope(name):
    return (name.startswith(('backend/', 'frontend/', 'data/')) or
            name in {'Dockerfile', 'pyproject.toml'}) and '__pycache__' not in name and not name.endswith(('.pyc', '/'))


def normalized(name, payload):
    text = Path(name).suffix in {'.py', '.js', '.css', '.html', '.json', '.toml', '.txt', '.csv', '.tsv', '.svg', '.md'} or name == 'Dockerfile'
    return payload.replace(b'\r\n', b'\n') if text else payload


git = ['git', '-c', f'safe.directory={root.as_posix()}']
if args.revision:
    names = subprocess.check_output(git + ['ls-tree', '-r', '--name-only', args.revision], cwd=root).decode().splitlines()
else:
    names = [p.relative_to(root).as_posix() for base in ('backend', 'frontend', 'data') for p in (root/base).rglob('*') if p.is_file()]
    names += ['Dockerfile', 'pyproject.toml']
names = {n for n in names if in_scope(n)}
mismatches = []
with zipfile.ZipFile(args.archive) as archive:
    deployed = {n for n in archive.namelist() if in_scope(n)}
    for name in sorted(names | deployed):
        if name not in names or name not in deployed:
            mismatches.append(name)
            continue
        local = subprocess.check_output(git + ['show', f'{args.revision}:{name}'], cwd=root) if args.revision else (root/name).read_bytes()
        if normalized(name, local) != normalized(name, archive.read(name)):
            mismatches.append(name)
print(f'Compared {len(deployed)} deployed runtime/config/dependency files; mismatches: {len(mismatches)}')
for name in mismatches:
    print(name)
raise SystemExit(bool(mismatches))
