#!/usr/bin/env python3
"""Refresh the auto-generated status block in README.md.

Uses only the Python standard library and the public GitHub API.
Shows aggregate numbers only (no repository names).
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request

USER = os.environ.get("GH_USER", "qiau")
README = "README.md"
START, END = "<!--STATUS:START-->", "<!--STATUS:END-->"

THOUGHTS = [
    "Automate the boring part, then understand the rest.",
    "Make it work, make it right, make it observable.",
    "Small commits, clear intent.",
    "Reliable beats clever.",
    "If it can break, measure it.",
    "Read the logs before guessing.",
    "Write code the next person will thank you for.",
    "Consistency beats intensity.",
    "Ship small, learn fast.",
    "A good dashboard is a good conversation with your system.",
    "Delete the code you no longer need.",
    "Docs are part of the feature.",
    "Debug with curiosity, not frustration.",
    "Learn a little every day.",
]


def fetch_user(user):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-status-updater",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"https://api.github.com/users/{user}", headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def age_label(created_at, today):
    created = dt.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").date()
    months = (today.year - created.year) * 12 + (today.month - created.month)
    if today.day < created.day:
        months -= 1
    years, rest = divmod(max(months, 0), 12)
    return f"{years}y {rest}m"


def render(data, today):
    thought = THOUGHTS[today.timetuple().tm_yday % len(THOUGHTS)]
    rows = [
        ("synced", f"{today.isoformat()} (UTC)"),
        ("uptime", f"{age_label(data['created_at'], today)} on GitHub"),
        ("public repos", str(data.get("public_repos", "-"))),
        ("followers", str(data.get("followers", "-"))),
        ("thought", thought),
    ]
    width = max(len(key) for key, _ in rows)
    body = "\n".join(f"  {key.ljust(width)}  {value}" for key, value in rows)
    return "```text\nraihan@fullstack:~$ ./status.sh\n\n" + body + "\n```"


def replace_block(text, block):
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        return None
    replacement = f"{START}\n{block}\n{END}"
    return pattern.sub(lambda _m: replacement, text, count=1)


def main():
    try:
        data = fetch_user(USER)
    except Exception as exc:  # network or API problem: keep the old block
        print(f"Could not fetch GitHub data ({exc}); leaving README unchanged.")
        return 0

    today = dt.datetime.now(dt.timezone.utc).date()
    with open(README, encoding="utf-8") as fh:
        original = fh.read()

    updated = replace_block(original, render(data, today))
    if updated is None:
        print(f"Markers {START} / {END} not found in {README}.")
        return 1
    if updated != original:
        with open(README, "w", encoding="utf-8") as fh:
            fh.write(updated)
        print("README status block updated.")
    else:
        print("No changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
