"""
fetch_data.py
Fetches World Cup 2026 data from football-data.org API.
Returns a structured dict with standings, finished matches, and upcoming matches.

Usage:
  Set FOOTBALL_API_KEY environment variable, then run:
  python fetch_data.py
"""

import os
import json
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get("FOOTBALL_API_KEY", "4a734c692bab432985cff651f0b17bac")
BASE_URL = "https://api.football-data.org/v4"
COMPETITION = "WC"

HEADERS = {
    "X-Auth-Token": API_KEY
}


def get(endpoint, params=None):
    """Make a GET request and return parsed JSON."""
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_standings():
    """Fetch group stage standings (all groups)."""
    data = get(f"/competitions/{COMPETITION}/standings")
    groups = []
    for standing in data.get("standings", []):
        group = {
            "name": standing["group"],  # e.g. "GROUP_A"
            "teams": []
        }
        for row in standing["table"]:
            group["teams"].append({
                "name": row["team"]["name"],
                "played": row["playedGames"],
                "won": row["won"],
                "draw": row["draw"],
                "lost": row["lost"],
                "goals_for": row["goalsFor"],
                "goals_against": row["goalsAgainst"],
                "points": row["points"],
            })
        groups.append(group)
    return groups


def fetch_finished_matches():
    """Fetch matches that have already been played."""
    data = get(f"/competitions/{COMPETITION}/matches", params={"status": "FINISHED"})
    matches = []
    for m in data.get("matches", []):
        matches.append({
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "home_score": m["score"]["fullTime"]["home"],
            "away_score": m["score"]["fullTime"]["away"],
            "group": m.get("group", ""),
            "stage": m["stage"],
            "utc_date": m["utcDate"],
        })
    return matches


def fetch_upcoming_matches():
    """Fetch scheduled (not yet played) matches."""
    data = get(f"/competitions/{COMPETITION}/matches", params={"status": "SCHEDULED"})
    matches = []
    for m in data.get("matches", []):
        matches.append({
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "group": m.get("group", ""),
            "stage": m["stage"],
            "utc_date": m["utcDate"],
        })
    return matches


def fetch_live_matches():
    """Fetch any currently live matches."""
    data = get(f"/competitions/{COMPETITION}/matches", params={"status": "IN_PLAY"})
    matches = []
    for m in data.get("matches", []):
        matches.append({
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "home_score": m["score"]["fullTime"]["home"],
            "away_score": m["score"]["fullTime"]["away"],
            "group": m.get("group", ""),
            "stage": m["stage"],
            "utc_date": m["utcDate"],
        })
    return matches


def fetch_all():
    print("Fetching finished matches...")
    finished = fetch_finished_matches()

    print("Fetching upcoming matches...")
    upcoming = fetch_upcoming_matches()

    print("Fetching live matches...")
    live = fetch_live_matches()

    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "standings": [],  # skip for now
        "finished_matches": finished,
        "upcoming_matches": upcoming,
        "live_matches": live,
    }


if __name__ == "__main__":
    data = fetch_all()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    with open("wc_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("\nSaved to wc_data.json")