"""Validate public project artifacts and local documentation links."""
from pathlib import Path
import re
from PIL import Image

root = Path(__file__).resolve().parent
repo = root.parents[1]
required = [
    'README.md', 'START_HERE.md', 'DEVPOST_PROJECT_OVERVIEW.md',
    'DEVPOST_PROJECT_DETAILS.md', 'BUILT_WITH.md', 'SUBMISSION_LINKS.md',
    'ARCHITECTURE_EXPLANATION.md', 'GOOGLE_CLOUD_PROOF.md',
    'TESTING_INSTRUCTIONS.md', 'GALLERY_PLAN.md', 'HACKATHON_COMPLIANCE.md',
    'fynura_architecture.png', 'fynura_architecture.svg',
    'fynura-thumbnail.png', 'media/README.md',
    'media/final-hero.png', 'media/final-global-map.png',
    'media/final-history.png', 'media/final-cusum.png',
    'media/final-researched-brief.png', 'media/final-infographic-full.png',
    'media/final-infographic.svg',
]
for name in required:
    assert (root / name).is_file(), name
for path in [*(repo / 'docs').rglob('*.md'), repo / 'README.md']:
    content = path.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)', content):
        if '://' in target or target.startswith('#'):
            continue
        assert (path.parent / target.split('#')[0]).exists(), f'{path}: broken link {target}'
    for phrase in ('still requires the owner', 'owner input required',
                   'owner must confirm', 'do not submit the package',
                   "owner's final seven checks"):
        assert phrase not in content.lower(), f'{path}: private workflow language'
assert Image.open(root / 'fynura_architecture.png').size == (1920, 1080)
assert Image.open(root / 'fynura-thumbnail.png').size == (1500, 1000)
assert Image.open(root / 'media/final-infographic-full.png').size == (1200, 2972)
for left, right in [
    ('DEVPOST_PROJECT_DETAILS.md', 'devpost-about.md'),
    ('fynura_architecture.png', 'fynura-architecture.png'),
    ('fynura_architecture.svg', 'fynura-architecture.svg'),
]:
    assert (root / left).read_bytes() == (root / right).read_bytes(), right
print(f'PASS: {len(required)} public artifacts, documentation links, image dimensions and aliases.')
