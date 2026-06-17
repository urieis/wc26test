"""
fetch_data.py
Fetches World Cup 2026 data from ESPN unofficial API.
No API key required.

Usage:
  python fetch_data.py
"""

import json
import requests
from datetime import datetime, timezone, timedelta

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"
COMPETITION = "fifa.world"  # ESPN competition ID for FIFA World Cup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

ISRAEL_OFFSET = 3  # IDT = UTC+3


def get(url, params=None):
    response = requests.get(url, headers=HEADERS, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def fetch_scoreboard():
    """Fetch all tournament matches using a full date range."""
    url = f"{BASE_URL}/{COMPETITION}/scoreboard"
    # WC 2026 runs June 11 - July 19, 2026
    return get(url, params={"dates": "20260611-20260719", "limit": 200})


def fetch_standings():
    """Fetch group standings from ESPN."""
    url = f"{BASE_URL}/{COMPETITION}/standings"
    try:
        return get(url)
    except Exception as e:
        print(f"  Standings fetch failed: {e}")
        return None


def parse_matches(scoreboard_data):
    """Parse ESPN scoreboard into finished, live, and upcoming matches."""
    finished, live, upcoming = [], [], []

    events = scoreboard_data.get("events", [])
    for event in events:
        competitions = event.get("competitions", [])
        for comp in competitions:
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            home_name = home.get("team", {}).get("displayName", "Unknown")
            away_name = away.get("team", {}).get("displayName", "Unknown")
            home_score = home.get("score", "0")
            away_score = away.get("score", "0")

            status = comp.get("status", {})
            status_type = status.get("type", {}).get("name", "STATUS_SCHEDULED")
            print(f"  DEBUG status: {status_type} | {home_name} vs {away_name}")
            utc_date = comp.get("date", "")

            notes = comp.get("notes", [])
            group = ""
            for note in notes:
                headline = note.get("headline", "")
                if "Group" in headline:
                    group = headline
                    break

            entry = {
                "home": home_name,
                "away": away_name,
                "group": group,
                "stage": "GROUP_STAGE",
                "utc_date": utc_date,
            }

            if status_type == "STATUS_FINAL":
                entry["home_score"] = int(home_score) if home_score else 0
                entry["away_score"] = int(away_score) if away_score else 0
                finished.append(entry)
            elif status_type in ("STATUS_IN_PROGRESS", "STATUS_HALFTIME"):
                entry["home_score"] = int(home_score) if home_score else 0
                entry["away_score"] = int(away_score) if away_score else 0
                live.append(entry)
            else:
                upcoming.append(entry)

    return finished, live, upcoming


def parse_standings(standings_data):
    """Parse ESPN standings into our format."""
    if not standings_data:
        return []

    groups = []
    try:
        groups_raw = standings_data.get("standings", {}).get("groups", [])
        for group_raw in groups_raw:
            group_name = group_raw.get("name", "")
            teams = []
            for entry in group_raw.get("standings", {}).get("entries", []):
                team = entry.get("team", {})
                stats = {s["name"]: s["value"] for s in entry.get("stats", [])}
                teams.append({
                    "name": team.get("displayName", ""),
                    "played": int(stats.get("gamesPlayed", 0)),
                    "won": int(stats.get("wins", 0)),
                    "draw": int(stats.get("ties", 0)),
                    "lost": int(stats.get("losses", 0)),
                    "goals_for": int(stats.get("pointsFor", 0)),
                    "goals_against": int(stats.get("pointsAgainst", 0)),
                    "points": int(stats.get("points", 0)),
                })
            if teams:
                groups.append({"name": group_name, "teams": teams})
    except Exception as e:
        print(f"  Could not parse standings: {e}")
        return []

    return groups


def fetch_all():
    print("Fetching scoreboard (matches)...")
    scoreboard = fetch_scoreboard()
    finished, live, upcoming = parse_matches(scoreboard)
    print(f"  Found: {len(finished)} finished, {len(live)} live, {len(upcoming)} upcoming")

    print("Fetching standings...")
    standings_raw = fetch_standings()
    standings = parse_standings(standings_raw)
    print(f"  Found: {len(standings)} groups in standings")

    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "standings": standings,
        "finished_matches": finished,
        "upcoming_matches": upcoming,
        "live_matches": live,
    }


if __name__ == "__main__":
    data = fetch_all()
    print("\n--- SUMMARY ---")
    print(f"Finished matches: {len(data['finished_matches'])}")
    print(f"Upcoming matches: {len(data['upcoming_matches'])}")
    print(f"Live matches:     {len(data['live_matches'])}")
    print(f"Standings groups: {len(data['standings'])}")

    with open("wc_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("\nSaved to wc_data.json")