"""
tools.py  —  Layer 3: Claude tool definitions + execution
----------------------------------------------------------
This file is the bridge between Claude and your NBA data.

TWO things live here:
  1. TOOL_DEFINITIONS  — JSON schemas that tell Claude what tools exist
                         and what arguments they accept.
  2. execute_tool()    — The function that actually RUNS a tool
                         when Claude decides to call one.

WHY keep these together?
  The schema and the implementation are tightly coupled.
  If you add a new parameter to a tool, you need to update both.
  Same file = impossible to forget one.

HOW Claude tool use works (important to understand!):
  1. You send Claude a message + the list of TOOL_DEFINITIONS.
  2. Claude reads your question and decides which tool to call.
  3. Claude returns a special "tool_use" response with:
       - the tool name  (e.g. "get_player_stats")
       - the arguments  (e.g. {"player_name": "LeBron James"})
  4. YOUR CODE calls execute_tool() with those arguments.
  5. You send the result back to Claude.
  6. Claude reads the result and writes a final answer.

  Claude never directly calls your Python functions —
  it just TELLS you which one to call. You run it.
  This keeps Claude in control of reasoning, you in control of execution.
"""

import json
from nba_api import (
    fetch_player,
    fetch_season_averages,
    fetch_recent_games,
    fetch_standings,
    fetch_team_by_name,
)


# ─────────────────────────────────────────────
# Tool definitions — what Claude sees
# ─────────────────────────────────────────────
#
# Each tool definition has three parts:
#   name        — the identifier Claude will use when calling it
#   description — CRITICAL. Claude reads this to decide WHEN to call the tool.
#                 Write it like you're explaining to a smart intern.
#   input_schema — JSON Schema defining the parameters Claude must provide.
#
# Think of this as the "API contract" between you and Claude.

TOOL_DEFINITIONS = [
    {
        "name": "get_player_stats",
        "description": (
            "Get a player's season averages including points, rebounds, assists, "
            "steals, blocks, and shooting percentages. "
            "Use this when the user asks about a player's stats, averages, or performance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "The player's name, e.g. 'LeBron James' or 'Steph Curry'",
                },
                "season": {
                    "type": "integer",
                    "description": "The season start year. 2024 means the 2024-25 season. Defaults to 2024.",
                },
            },
            "required": ["player_name"],
        },
    },
    {
        "name": "get_team_recent_games",
        "description": (
            "Get the most recent games played by a team, including scores and dates. "
            "Use this when the user asks about a team's recent results, record, or game history."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "The team name or city, e.g. 'Lakers', 'Golden State Warriors', 'BOS'",
                },
                "num_games": {
                    "type": "integer",
                    "description": "How many recent games to fetch. Defaults to 5.",
                },
            },
            "required": ["team_name"],
        },
    },
    {
        "name": "get_standings",
        "description": (
            "Get the current NBA standings, optionally filtered by conference. "
            "Use this when the user asks about standings, rankings, records, or "
            "which teams are in playoff position."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "conference": {
                    "type": "string",
                    "enum": ["East", "West", "all"],
                    "description": "Which conference standings to return. Use 'all' for both.",
                },
            },
            "required": ["conference"],
        },
    },
    {
        "name": "get_team_info",
        "description": (
            "Look up basic info about a team: conference, division, and abbreviation. "
            "Useful as a first step before fetching games or standings for a specific team."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "The team name, city, or abbreviation.",
                },
            },
            "required": ["team_name"],
        },
    },
]


# ─────────────────────────────────────────────
# Tool executor — what YOUR code runs
# ─────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Routes a tool call from Claude to the right Python function.

    Returns a JSON string — Claude needs text back, not a Python dict.

    WHY return a string?
      The Claude API expects tool results as text content.
      json.dumps() converts our dict into a clean JSON string
      that Claude can read and reason about.
    """
    try:
        if tool_name == "get_player_stats":
            player = fetch_player(tool_input["player_name"])
            if "error" in player:
                return json.dumps(player)

            season = tool_input.get("season", 2024)
            stats = fetch_season_averages(player["id"], season)

            # Merge player info + stats into one result
            return json.dumps({**player, **stats})

        elif tool_name == "get_team_recent_games":
            team = fetch_team_by_name(tool_input["team_name"])
            if "error" in team:
                return json.dumps(team)

            num_games = tool_input.get("num_games", 5)
            games = fetch_recent_games(team["id"], num_games)
            return json.dumps({"team": team["name"], "recent_games": games})

        elif tool_name == "get_standings":
            standings = fetch_standings(tool_input.get("conference", "all"))
            return json.dumps({"standings": standings})

        elif tool_name == "get_team_info":
            team = fetch_team_by_name(tool_input["team_name"])
            return json.dumps(team)

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        # Return errors as JSON so Claude can explain them to the user
        return json.dumps({"error": str(e)})