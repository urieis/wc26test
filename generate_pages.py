"""
generate_pages.py
Reads wc_data.json, calls Claude API, generates English and Hebrew HTML pages.

Usage:
  Set ANTHROPIC_API_KEY environment variable, then run:
  python generate_pages.py
"""

import os
import json
import anthropic
from datetime import datetime, timezone, timedelta
from pathlib import Path

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ISRAEL_OFFSET = 3  # IDT = UTC+3

# Paths
DATA_FILE = "wc_data.json"
PROMPTS_DIR = Path("prompts")
OUTPUT_DIR = Path("output")


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt(lang):
    path = PROMPTS_DIR / f"{lang}.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_today_israel():
    """Return today's date in Israel time as YYYY-MM-DD string."""
    utc_now = datetime.now(timezone.utc)
    israel_now = utc_now + timedelta(hours=ISRAEL_OFFSET)
    return israel_now.strftime("%Y-%m-%d")


def build_user_message(data):
    """Build the user message containing the data payload."""
    today = get_today_israel()
    payload = {
        **data,
        "today_date": today,
        "israel_offset": ISRAEL_OFFSET,
    }
    return f"Generate the page for today ({today}) using this data:\n\n{json.dumps(payload, indent=2, ensure_ascii=False)}"


def generate_page(lang, system_prompt, user_message):
    """Call Claude API and return the generated HTML."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"  Calling Claude for {lang.upper()} page...")
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    html = message.content[0].text

    # Strip markdown code fences if Claude wraps in ```html ... ```
    if html.startswith("```"):
        lines = html.split("\n")
        html = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return html


def save_page(lang, html):
    """Save generated HTML to output directory."""
    lang_dir = OUTPUT_DIR / lang
    lang_dir.mkdir(parents=True, exist_ok=True)
    output_path = lang_dir / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved: {output_path}")
    return output_path


def main():
    print("Loading data...")
    data = load_data()
    print(f"  {len(data['finished_matches'])} finished matches")
    print(f"  {len(data['upcoming_matches'])} upcoming matches")
    print(f"  Standings: {'available' if data['standings'] else 'empty (will be computed by Claude)'}")

    user_message = build_user_message(data)

    for lang in ["en", "he"]:
        print(f"\nGenerating {lang.upper()} page...")
        system_prompt = load_prompt(lang)
        html = generate_page(lang, system_prompt, user_message)
        path = save_page(lang, html)
        print(f"  Done. ({len(html):,} characters)")

    print("\nAll pages generated successfully.")
    print(f"  English: output/en/index.html")
    print(f"  Hebrew:  output/he/index.html")


if __name__ == "__main__":
    main()
