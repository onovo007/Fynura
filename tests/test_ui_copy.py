from pathlib import Path


def test_app_authored_ui_copy_has_no_em_dashes():
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    forbidden = (chr(0x2014), "&mdash;", "&#8212;", "&#x2014;", r"\u2014")
    for path in frontend.rglob("*"):
        if path.suffix not in {".html", ".js", ".css", ".svg"}:
            continue
        content = path.read_text(encoding="utf-8")
        assert not any(token in content for token in forbidden), str(path)


def test_public_signal_review_does_not_render_unsupported_ifr_copy():
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    signal_code = (frontend / "early-signals.js").read_text(encoding="utf-8")
    assert "IFR: Not estimable" not in signal_code


def test_public_section_numbering_finishes_with_trust_as_section_seven():
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    visuals = (frontend / "visuals.js").read_text(encoding="utf-8")
    assert "07 / TRUST & METHODOLOGY" in visuals
    assert "05 / TRUST & METHODOLOGY" not in visuals
