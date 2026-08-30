from pathlib import Path


def test_app_authored_ui_copy_has_no_em_dashes():
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    forbidden = (chr(0x2014), "&mdash;", "&#8212;", "&#x2014;", r"\u2014")
    for path in frontend.rglob("*"):
        if path.suffix not in {".html", ".js", ".css", ".svg"}:
            continue
        content = path.read_text(encoding="utf-8")
        assert not any(token in content for token in forbidden), str(path)
