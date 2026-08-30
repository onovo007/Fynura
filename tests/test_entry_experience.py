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
    for name in ('map', 'analysis', 'communities', 'surveillance', 'protection'):
        asset = ROOT / f'frontend/assets/entry-{name}.webp'
        assert asset.is_file()
        assert asset.stat().st_size < 350_000
    style = (ROOT / 'frontend/entry-story.css').read_text(encoding='utf-8')
    assert 'entry-analysis.webp' in style and 'entry-communities.webp' in style
    assert 'prefers-reduced-motion' in style
    assert 'animation-play-state:paused' in style


def test_five_frame_story_keeps_accessibility_controls():
    script = (ROOT / 'frontend/entry-story.js').read_text(encoding='utf-8')
    style = (ROOT / 'frontend/entry-sequence.css').read_text(encoding='utf-8')
    for name in ('map', 'analysis', 'communities', 'surveillance', 'protection'):
        assert f"['{name}'" in script
    assert '10000' in script
    assert 'opacity 1.3s' in style
    assert 'prefers-reduced-motion' in style
    assert 'clearTimeout(timer)' in script
    assert 'aria-pressed' in script
    assert '/static/entry-sequence.css?v=2' in script
    assert '74svh' in style
    assert script.index("['surveillance'") < script.index("['analysis'") < script.index("['protection'") < script.index("['map'") < script.index("['communities'")


def test_main_app_has_logout_and_cache_protection():
    from fastapi.testclient import TestClient
    from backend.main import app

    page = BeautifulSoup((ROOT / 'frontend/index.html').read_text(encoding='utf-8'), 'html.parser')
    assert page.select_one('#app-signout').get_text() == 'Sign out'
    assert page.select_one('script[src="/static/session-controls.js?v=1"]')
    script = (ROOT / 'frontend/session-controls.js').read_text(encoding='utf-8')
    assert "/api/auth/logout" in script
    assert "location.replace('/welcome')" in script
    client = TestClient(app)
    response = client.post('/api/auth/logout')
    assert response.status_code == 204
    assert 'Max-Age=0' in response.headers['set-cookie']
    assert response.headers['cache-control'] == 'no-store'
    assert client.get('/welcome').headers['cache-control'] == 'no-store'
    assert client.get('/static/session-controls.js').headers['cache-control'] == 'no-cache'


def test_transition_only_follows_successful_onboarding():
    script = (ROOT / 'frontend/auth.js').read_text(encoding='utf-8')
    assert script.index('if (!response.ok)') < script.index("classList.add('is-entering')")
    assert "prefers-reduced-motion: reduce" in script
    assert "matches?0:450" in script
