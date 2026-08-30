from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def test_entry_preserves_google_identity_and_privacy_contract():
    page = BeautifulSoup((ROOT / 'frontend/welcome.html').read_text(encoding='utf-8'), 'html.parser')
    assert page.select_one('#google-signin')['type'] == 'button'
    assert page.select_one('#signed-in-email')['type'] == 'email'
    assert page.select_one('#signed-in-email').has_attr('readonly')
    assert page.select_one('[name=country]').has_attr('required')
    assert page.select_one('[name=privacy_acknowledged]').has_attr('required')
    assert page.select_one('#status')['aria-live'] == 'polite'
    assert 'not live surveillance data' in page.get_text()


def test_entry_assets_optimized_and_explicitly_mapped():
    for name in ('map', 'analysis', 'communities'):
        asset = ROOT / f'frontend/assets/entry-{name}.webp'
        assert asset.is_file()
        assert asset.stat().st_size < 350_000
    style = (ROOT / 'frontend/entry-story.css').read_text(encoding='utf-8')
    assert 'entry-analysis.webp' in style and 'entry-communities.webp' in style
    assert 'prefers-reduced-motion' in style
    assert 'animation-play-state:paused' in style


def test_transition_only_follows_successful_onboarding():
    script = (ROOT / 'frontend/auth.js').read_text(encoding='utf-8')
    assert script.index('if (!response.ok)') < script.index("classList.add('is-entering')")
    assert "prefers-reduced-motion: reduce" in script
    assert "matches?0:450" in script
