from pathlib import Path

from backend.main import app


ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ("monitor", "verify", "detect", "advise", "learn")


def test_workspace_routes_and_security_gate_are_registered():
    routes = {route.path for route in app.routes}
    source = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
    for workspace in WORKSPACES:
        assert f"/{workspace}" in routes
        assert f'"/{workspace}"' in source
    assert "path in workspace_routes" in source
    assert 'RedirectResponse("/welcome"' in source


def test_index_exposes_the_five_workspace_tabs():
    page = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    for workspace in WORKSPACES:
        assert f'data-workspace-link="{workspace}"' in page


def test_shell_defines_route_state_accessibility_and_legacy_links():
    script = (ROOT / "frontend" / "app-shell.js").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "app-shell.css").read_text(encoding="utf-8")
    assert "popstate" in script
    assert "aria-current" in script
    assert "prefers-reduced-motion" in script
    assert "historical-evidence':'detect'" in script
    assert "Open the Ask Fynura workspace" in script
    assert "main>section[hidden]" in css
