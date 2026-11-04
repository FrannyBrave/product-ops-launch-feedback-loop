"""Offline tests: check rendering and safety checks using hand-written fixtures.
Run with:  python tests/test_render.py
No API key needed."""

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "workflows"))

import feedback_triage  # noqa: E402
import release_briefings  # noqa: E402


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


def test_release():
    release = load("sample_data/shipped_changes.json")
    result = load("tests/fixtures/release_response.json")
    warnings = release_briefings.validate(result, release)
    assert any("unknown change id 'BL-999'" in w for w in warnings), warnings
    assert any("Internal-only change 'BL-433'" in w for w in warnings), warnings
    assert any("'BL-430' does not appear" in w for w in warnings), warnings
    files = release_briefings.render(result, release, warnings)
    assert set(files) == {"customer-release-notes.md", "support-briefing.md", "sales-briefing.md",
                          "implementations-briefing.md", "needs-info.md"}
    assert "DRAFT" in files["customer-release-notes.md"]
    assert "Borrower portal: upload from phone camera" in files["needs-info.md"]
    print("release_briefings: OK")


def test_triage():
    with open(os.path.join(ROOT, "sample_data/feedback.csv"), newline="", encoding="utf-8") as f:
        feedback = list(csv.DictReader(f))
    routing = load("config/routing.json")
    result = load("tests/fixtures/triage_response.json")
    files = feedback_triage.render(result, feedback, routing)
    assert "ESCALATE NOW" in files["triage-table.md"]
    assert "Product Ops (manual review)" in files["triage-table.md"]     # unclear item routed to manual review
    assert "was not triaged" in files["triage-table.md"]                 # items the response skipped are reported
    assert "| 3: Harbor Credit Union, Lakeside Lending, Riverbend Financial |" in files["themes.md"]  # counted by code
    assert "Sam (Implementations)" in files["follow-ups.md"]
    assert "PM, Pipeline (3 items)" in files["pm-digests.md"]
    print("feedback_triage: OK")


if __name__ == "__main__":
    test_release()
    test_triage()
    print("All tests passed.")
