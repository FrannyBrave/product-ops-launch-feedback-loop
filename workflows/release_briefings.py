"""Release briefings: turn a list of shipped changes into
customer release notes and briefings for Support, Sales and Implementations.

Usage:
    python workflows/release_briefings.py --input sample_data/shipped_changes.json --out examples/release
    python workflows/release_briefings.py --input sample_data/shipped_changes.json --dry-run

Rules the workflow follows:
  * It only uses facts from the input file. If something is missing, it is
    listed under "needs info" with a question for the PM, never invented.
  * Every output is marked DRAFT for a person to review.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from claude_client import DRAFT_BANNER, call_claude_structured, save, save_json  # noqa: E402

TEAMS = {
    "support": "Support: what changed, what customers may notice, what to watch for, and likely questions with answers.",
    "sales": "Sales: the customer problem it solves, who it matters to, and short talking points. No promises beyond the input.",
    "implementations": "Implementations: configuration steps, which customers are affected, and rollout notes.",
}

SYSTEM_PROMPT = """You are a product operations assistant at a B2B software company.
You turn a list of shipped product changes into release communications.

Strict rules:
1. Use ONLY facts stated in the input. Never invent dates, numbers, customer names, configuration steps or benefits.
2. If a change is missing information a team needs (for example who is affected, or whether configuration is required),
   write "TBD (see needs info)" in that spot and add an entry to "needs_info" with a specific question for the PM.
3. Internal-only changes do not get customer release notes.
4. Write plainly and briefly. No marketing hype.
5. Submit your answer with the submit_result tool."""

_BRIEFING_ITEM = {
    "type": "object",
    "properties": {
        "change_id": {"type": "string"},
        "what_changed": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "action_for_team": {"type": "string"},
        "likely_questions": {
            "type": "array",
            "items": {"type": "object", "properties": {"q": {"type": "string"}, "a": {"type": "string"}},
                      "required": ["q", "a"]},
        },
    },
    "required": ["change_id", "what_changed", "why_it_matters", "action_for_team", "likely_questions"],
}

SCHEMA = {
    "type": "object",
    "properties": {
        "customer_release_notes": {
            "type": "array",
            "items": {"type": "object",
                      "properties": {"change_id": {"type": "string"}, "headline": {"type": "string"},
                                     "summary": {"type": "string"}},
                      "required": ["change_id", "headline", "summary"]},
        },
        "briefings": {
            "type": "object",
            "properties": {team: {"type": "array", "items": _BRIEFING_ITEM} for team in TEAMS},
            "required": list(TEAMS),
        },
        "needs_info": {
            "type": "array",
            "items": {"type": "object",
                      "properties": {"change_id": {"type": "string"}, "missing": {"type": "string"},
                                     "question_for_pm": {"type": "string"}},
                      "required": ["change_id", "missing", "question_for_pm"]},
        },
    },
    "required": ["customer_release_notes", "briefings", "needs_info"],
}


def build_user_prompt(release: dict) -> str:
    team_guidance = "\n".join(f"- {text}" for text in TEAMS.values())
    return (
        "Write release communications for this release.\n\n"
        f"What each team needs:\n{team_guidance}\n\n"
        "Shipped changes (JSON):\n"
        f"{json.dumps(release, indent=2)}"
    )


def validate(result: dict, release: dict) -> list:
    """Check Claude's answer against the input. Returns a list of warnings."""
    warnings = []
    known_ids = {c["id"] for c in release["changes"]}

    referenced = [n["change_id"] for n in result.get("customer_release_notes", [])]
    for team in TEAMS:
        referenced += [b["change_id"] for b in result.get("briefings", {}).get(team, [])]
    referenced += [n["change_id"] for n in result.get("needs_info", [])]

    for cid in set(referenced) - known_ids:
        warnings.append(f"Output mentions unknown change id '{cid}'.")
    internal_ids = {c["id"] for c in release["changes"] if c.get("internal_only")}
    for cid in known_ids - set(referenced) - internal_ids:  # internal-only changes may be left out
        warnings.append(f"Change '{cid}' does not appear anywhere in the output.")
    for c in release["changes"]:
        if c.get("internal_only") and c["id"] in [n["change_id"] for n in result.get("customer_release_notes", [])]:
            warnings.append(f"Internal-only change '{c['id']}' appears in customer release notes.")
    return warnings


def render(result: dict, release: dict, warnings: list) -> dict:
    """Turn the JSON answer into Markdown files. Returns {filename: content}."""
    titles = {c["id"]: c["title"] for c in release["changes"]}
    name = release.get("release", "release")
    files = {}

    lines = [f"# Release notes: {name}\n", DRAFT_BANNER]
    for note in result.get("customer_release_notes", []):
        lines.append(f"### {note['headline']}\n\n{note['summary']}\n")
    files["customer-release-notes.md"] = "\n".join(lines)

    for team in TEAMS:
        lines = [f"# {team.title()} briefing: {name}\n", DRAFT_BANNER]
        for item in result.get("briefings", {}).get(team, []):
            lines.append(f"## {titles.get(item['change_id'], item['change_id'])} ({item['change_id']})\n")
            lines.append(f"**What changed:** {item['what_changed']}\n")
            lines.append(f"**Why it matters:** {item['why_it_matters']}\n")
            lines.append(f"**What you need to do:** {item['action_for_team']}\n")
            if item.get("likely_questions"):
                lines.append("**Likely questions**\n")
                for qa in item["likely_questions"]:
                    lines.append(f"- *{qa['q']}* {qa['a']}")
                lines.append("")
        files[f"{team}-briefing.md"] = "\n".join(lines)

    lines = [f"# Needs info before sending: {name}\n",
             "These gaps were flagged instead of guessed. Send each question to the PM.\n",
             "| Change | Missing | Question for the PM |", "|---|---|---|"]
    for n in result.get("needs_info", []):
        lines.append(f"| {titles.get(n['change_id'], n['change_id'])} | {n['missing']} | {n['question_for_pm']} |")
    if warnings:
        lines += ["", "## Automatic checks", ""] + [f"- {w}" for w in warnings]
    files["needs-info.md"] = "\n".join(lines) + "\n"
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="JSON file of shipped changes")
    parser.add_argument("--out", default="examples/release", help="folder for the Markdown outputs")
    parser.add_argument("--dry-run", action="store_true", help="print the prompt without calling Claude")
    parser.add_argument("--from-response", help="render from a saved JSON response instead of calling Claude")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        release = json.load(f)
    user_prompt = build_user_prompt(release)

    if args.dry_run:
        print("=== SYSTEM PROMPT ===\n" + SYSTEM_PROMPT + "\n\n=== USER PROMPT ===\n" + user_prompt
              + "\n\n=== OUTPUT SCHEMA ===\n" + json.dumps(SCHEMA, indent=2))
        return

    if args.from_response:
        with open(args.from_response, encoding="utf-8") as f:
            result = json.load(f)
    else:
        print(f"Asking Claude to draft communications for {len(release['changes'])} changes...")
        result = call_claude_structured(SYSTEM_PROMPT, user_prompt, SCHEMA)
        save_json(os.path.join(args.out, "raw-response.json"), result)

    warnings = validate(result, release)
    for filename, content in render(result, release, warnings).items():
        save(os.path.join(args.out, filename), content)
    flagged = len(result.get("needs_info", []))
    print(f"Done. {flagged} item(s) flagged for PM follow-up; {len(warnings)} automatic check warning(s).")


if __name__ == "__main__":
    main()
