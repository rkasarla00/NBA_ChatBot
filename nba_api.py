"""
nba_api.py  —  Layer 4: Raw NBA data fetching
----------------------------------------------
This file's only job is to talk to the balldontlie.io API
and return clean Python dictionaries.

WHY a separate file?
  Keeping API calls here means if the API ever changes,
  you only fix it in one place. The rest of your app
  doesn't know or care where the data comes from.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.balldontlie.io/v1"

def _headers() -> dict:
    """Returns auth headers for every request."""
    return {"Authorization": os.getenv("BALLDONTLIE_API_KEY", "")}


def _get(endpoint: str, params: dict = None) -> dict:
    """
    Central request helper — all API calls go through here.

    WHY centralise this?
      - One place to add error handling, retries, or logging later.
      - Keeps individual functions clean.
    """
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=_headers(), params=params or {})

    # Raise a clear error if the API returns 4xx / 5xx
    response.raise_for_status()
    return response.json()


# ─────────────────────────────────────────────
# Public functions — these are what tools.py calls
# ─────────────────────────────────────────────

def fetch_player(name: str) -> dict:
    """
    Search for a player by name and return their profile.

    balldontlie search is fuzzy — "LeBron" finds "LeBron James".
    We take the first result since it's almost always correct.
    """
    data = _get("players", {"search": name, "per_page": 1})
    players = data.get("data", [])

    if not players:
        return {"error": f"No player found matching '{name}'"}

    player = players[0]
    return {
        "id": player["id"],
        "name": f"{player['first_name']} {player['last_name']}",
        "position": player.get("position", "N/A"),
        "team": player.get("team", {}).get("full_name", "N/A"),
    }


def fetch_season_averages(player_id: int, season: int = 2024) -> dict:
    """
    Get a player's per-game averages for a given season.

    'season' means the year the season STARTED — so 2024 = 2024-25 season.
    balldontlie uses this convention throughout.
    """
    data = _get("season_averages", {
        "player_ids[]": player_id,
        "season": season,
    })

    stats = data.get("data", [])
    if not stats:
        return {"error": f"No stats found for player_id {player_id} in {season} season"}

    s = stats[0]
    return {
        "season": season,
        "games_played": s.get("games_played"),
        "pts": round(s.get("pts", 0), 1),
        "reb": round(s.get("reb", 0), 1),
        "ast": round(s.get("ast", 0), 1),
        "stl": round(s.get("stl", 0), 1),
        "blk": round(s.get("blk", 0), 1),
        "fg_pct": round(s.get("fg_pct", 0) * 100, 1),
        "fg3_pct": round(s.get("fg3_pct", 0) * 100, 1),
        "ft_pct": round(s.get("ft_pct", 0) * 100, 1),
    }


def fetch_recent_games(team_id: int, num_games: int = 5) -> list:
    """
    Get the most recent N games for a team.

    WHY team games instead of player games?
      balldontlie's free tier gives team-level game results easily.
      Individual player game logs require filtering box scores (more complex).
      We start simple here and can upgrade later.
    """
    data = _get("games", {
        "team_ids[]": team_id,
        "per_page": num_games,
        "seasons[]": 2024,
    })

    games = data.get("data", [])
    results = []

    for g in games:
        home = g["home_team"]["full_name"]
        visitor = g["visitor_team"]["full_name"]
        home_score = g.get("home_team_score", "TBD")
        visitor_score = g.get("visitor_team_score", "TBD")
        results.append({
            "date": g.get("date", "")[:10],  # trim to YYYY-MM-DD
            "matchup": f"{visitor} @ {home}",
            "score": f"{visitor_score} - {home_score}",
            "status": g.get("status", ""),
        })

    return results


def fetch_standings(conference: str = "all") -> list:
    """
    Get current standings.

    conference: "East", "West", or "all" for both.
    Note: balldontlie standings endpoint returns data sorted by wins.
    """
    data = _get("standings", {"season": 2024})
    teams = data.get("data", [])

    results = []
    for t in teams:
        conf = t.get("conference", "")
        # Filter by conference if requested
        if conference != "all" and conf.lower() != conference.lower():
            continue
        results.append({
            "team": t["team"]["full_name"],
            "conference": conf,
            "wins": t.get("wins", 0),
            "losses": t.get("losses", 0),
            "win_pct": round(t.get("wins", 0) / max(t.get("wins", 0) + t.get("losses", 0), 1), 3),
        })

    # Sort by win percentage descending
    results.sort(key=lambda x: x["win_pct"], reverse=True)
    return results


def fetch_team_by_name(name: str) -> dict:
    """Find a team by name and return its id and details."""
    data = _get("teams", {"per_page": 30})
    teams = data.get("data", [])

    name_lower = name.lower()
    for t in teams:
        if name_lower in t["full_name"].lower() or name_lower in t["abbreviation"].lower():
            return {
                "id": t["id"],
                "name": t["full_name"],
                "abbreviation": t["abbreviation"],
                "conference": t["conference"],
                "division": t["division"],
            }

    return {"error": f"No team found matching '{name}'"}