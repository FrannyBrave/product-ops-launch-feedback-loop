"""Feedback triage: classify customer feedback from Support, Sales and
Implementations, route each item to the right PM, find recurring themes,
and draft follow-up questions back to the people who submitted unclear items.

Usage:
    python workflows/feedback_triage.py --input sample_data/feedback.csv --routing config/routing.json --out examples/triage
    python workflows/feedback_triage.py --input sample_data/feedback.csv --routing config/routing.json --dry-run

Design choices:
  * Claude classifies and groups. The script does the routing and the counting,
    so routing always follows the routing table and theme counts are exact.
  * Unclear items are never guessed at: they get a question back to the submitter.
  * Urgent production issues are flagged to use the support escalation path.
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from claude_client import DRAFT_BANNER, call_claude_structured, save, save_json  # noqa: E402

SYSTEM_PROMPT = """You are a product operations assistant triaging customer feedback at a B2B software company.

For each feedback item:
- type: one of "bug", "feature_request", "question", "other"
- product_area: exactly one of the allowed areas you are given, or "Unclear" if the item doesn't say enough
- summary: one plain sentence, using only what the item says
- customer_impact: one sentence on the impact the item describes, or "Not stated"
- urgency: "high" (customer blocked or data at risk), "medium", or "low"
- escalate_now: true only if it describes a production outage or a customer completely blocked
- needs_clarification: true if a PM could not act on it as written
- clarifying_question: if needs_clarification is true, one specific question for the submitter, otherwise ""

Then group related items into themes (two or more items about the same underlying problem).

Rules: use ONLY what the items say. Do not guess product areas, impact or customers.
Submit your answer with the submit_result tool."""

SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["bug", "feature_request", "question", "other"]},
                    "product_area": {"type": "string"},
                    "summary": {"type": "string"},
                    "customer_impact": {"type": "string"},
                    "urgency": {"type": "string", "enum": ["high", "medium", "low"]},
                    "escalate_now": {"type": "boolean"},
                    "needs_clarification": {"type": "boolean"},
                    "clarifying_question": {"type": "string"},
                },
                "required": ["id", "type", "product_area", "summary", "customer_impact", "urgency",
                             "escalate_now", "needs_clarification", "clarifying_question"],
            },
        },
        "themes": {
            "type": "array",
            "items": {"type": "object",
                      "properties": {"theme": {"type": "string"},
                                     "item_ids": {"type": "array", "items": {"type": "string"}},
                                     "summary": {"type": "string"}},
                      "required": ["theme", "item_ids", "summary"]},
        },
    },
    "required": ["items", "themes"],
}


def load_feedback(path: str) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_user_prompt(feedback: list, areas: list) -> str:
    return (
        f"Allowed product areas: {json.dumps(areas)}\n\n"
        "Feedback items (JSON):\n"
        f"{json.dumps(feedback, indent=2)}"
    )


def route(item: dict, routing: dict) -> dict:
    """Look up the owner in the routing table. Unknown or unclear areas go to manual review."""
    return routing["areas"].get(item.get("product_area"), routing["unclear"])


def render(result: dict, feedback: list, routing: dict) -> dict:
    source = {row["id"]: row for row in feedback}
    items = result.get("items", [])
    files = {}
    warnings = []

    for item in items:
        if item["id"] not in source:
            warnings.append(f"Claude returned unknown item id '{item['id']}'.")
    for missing in set(source) - {i["id"] for i in items}:
        warnings.append(f"Item '{missing}' was not triaged. Review it by hand.")

    # 1. Full triage table
    lines = ["# Feedback triage\n", DRAFT_BANNER,
             "| ID | Customer | Type | Area | Urgency | Routed to | Summary |", "|---|---|---|---|---|---|---|"]
    for item in items:
        row = source.get(item["id"], {})
        owner = route(item, routing)["owner"]
        flag = " **ESCALATE NOW**" if item.get("escalate_now") else ""
        lines.append(f"| {item['id']} | {row.get('customer', '?')} | {item['type']} | {item['product_area']} | "
                     f"{item['urgency']}{flag} | {owner} | {item['summary']} |")
    if warnings:
        lines += ["", "## Automatic checks", ""] + [f"- {w}" for w in warnings]
    files["triage-table.md"] = "\n".join(lines) + "\n"

    # 2. One digest per PM
    by_owner = defaultdict(list)
    for item in items:
        if not item.get("needs_clarification"):
            by_owner[route(item, routing)["owner"]].append(item)
    lines = ["# PM digests\n", DRAFT_BANNER]
    for owner, owned in sorted(by_owner.items()):
        lines.append(f"## {owner} ({len(owned)} item{'s' if len(owned) != 1 else ''})\n")
        for item in sorted(owned, key=lambda i: {"high": 0, "medium": 1, "low": 2}.get(i["urgency"], 3)):
            row = source.get(item["id"], {})
            lines.append(f"- **[{item['urgency']}] {item['summary']}** ({row.get('customer', '?')}, "
                         f"from {row.get('submitted_by', '?')}, {item['id']})  \n  Impact: {item['customer_impact']}")
        lines.append("")
    files["pm-digests.md"] = "\n".join(lines)

    # 3. Themes, with counts computed here (not by the model)
    lines = ["# Recurring themes\n", DRAFT_BANNER, "| Theme | Customers | Items | Summary |", "|---|---|---|---|"]
    for theme in result.get("themes", []):
        ids = [i for i in theme["item_ids"] if i in source]
        customers = sorted({source[i]["customer"] for i in ids})
        lines.append(f"| {theme['theme']} | {len(customers)}: {', '.join(customers)} | {', '.join(ids)} | {theme['summary']} |")
    files["themes.md"] = "\n".join(lines) + "\n"

    # 4. Follow-ups back to submitters (closing the loop on unclear items)
    lines = ["# Follow-up questions to submitters\n", DRAFT_BANNER,
             "These items were too unclear to route. Each submitter gets a specific question.\n"]
    for item in items:
        if item.get("needs_clarification"):
            row = source.get(item["id"], {})
            lines.append(f"**To {row.get('submitted_by', '?')}** (about {row.get('customer', '?')}, {item['id']}):  \n"
                         f"Thanks for flagging this. To route it to the right PM: {item['clarifying_question']}\n")
    files["follow-ups.md"] = "\n".join(lines)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="CSV of feedback items")
    parser.add_argument("--routing", required=True, help="JSON routing table")
    parser.add_argument("--out", default="examples/triage", help="folder for the Markdown outputs")
    parser.add_argument("--dry-run", action="store_true", help="print the prompt without calling Claude")
    parser.add_argument("--from-response", help="render from a saved JSON response instead of calling Claude")
    args = parser.parse_args()

    feedback = load_feedback(args.input)
    with open(args.routing, encoding="utf-8") as f:
        routing = json.load(f)
    user_prompt = build_user_prompt(feedback, list(routing["areas"].keys()))

    if args.dry_run:
        print("=== SYSTEM PROMPT ===\n" + SYSTEM_PROMPT + "\n\n=== USER PROMPT ===\n" + user_prompt
              + "\n\n=== OUTPUT SCHEMA ===\n" + json.dumps(SCHEMA, indent=2))
        return

    if args.from_response:
        with open(args.from_response, encoding="utf-8") as f:
            result = json.load(f)
    else:
        print(f"Asking Claude to triage {len(feedback)} feedback items...")
        result = call_claude_structured(SYSTEM_PROMPT, user_prompt, SCHEMA)
        save_json(os.path.join(args.out, "raw-response.json"), result)

    for filename, content in render(result, feedback, routing).items():
        save(os.path.join(args.out, filename), content)
    unclear = sum(1 for i in result.get("items", []) if i.get("needs_clarification"))
    urgent = sum(1 for i in result.get("items", []) if i.get("escalate_now"))
    print(f"Done. {unclear} item(s) need clarification; {urgent} flagged for immediate escalation.")


if __name__ == "__main__":
    main()
