# NBA ChatBot

An AI-powered NBA analyst chatbot built with Claude and the balldontlie API. Ask it about player stats, team results, and standings — it uses live data to give accurate, conversational answers.

## How it works

The app implements an **agentic loop**: Claude receives your question, decides which data tools to call, fetches live NBA data, and synthesizes a response. Multi-step questions (e.g., "Compare LeBron and Curry") trigger multiple tool calls in sequence before a final answer is returned.

```
User question
     │
     ▼
  Claude (claude-sonnet-4-6)
     │
     ├── tool_use? → fetch NBA data → send results back → repeat
     │
     └── end_turn? → return final answer to user
```

### File structure

```
NBA_ChatBot/
├── main.py           # Terminal chat interface
├── streamlit_app.py  # Web UI (Streamlit)
├── agent.py          # Agentic loop — Claude + tool orchestration
├── tools.py          # Tool definitions (Claude's schema) + executor
├── nba_api.py        # balldontlie API client
├── requirements.txt
└── .env              # API keys (not committed)
```

Each file has a single responsibility:

| File | Role |
|---|---|
| `agent.py` | Drives the Claude loop; calls tools until a final answer is ready |
| `tools.py` | Defines what tools Claude can call and routes calls to `nba_api.py` |
| `nba_api.py` | Fetches raw data from balldontlie.io; returns clean dicts |
| `main.py` | Manages terminal conversation history; calls `run_agent()` |
| `streamlit_app.py` | Web UI; manages session state and displays chat |

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- A [balldontlie API key](https://www.balldontlie.io/) (free tier works)

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/your-username/NBA_ChatBot.git
cd NBA_ChatBot
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure API keys**

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_anthropic_key_here
BALLDONTLIE_API_KEY=your_balldontlie_key_here
```

## Running the app

**Terminal interface**

```bash
python main.py
```

**Web UI (Streamlit)**

```bash
streamlit run streamlit_app.py
```

Then open `http://localhost:8501` in your browser.

## Example questions

- "How is LeBron doing this season?"
- "Show me the Lakers' last 5 games"
- "What are the Western Conference standings?"
- "Compare Steph Curry and Kevin Durant's stats"

## Available tools

Claude can call four tools against the balldontlie API:

| Tool | What it fetches |
|---|---|
| `get_player_stats` | Season averages (pts, reb, ast, stl, blk, shooting %) |
| `get_team_recent_games` | Last N games with scores and dates |
| `get_standings` | League standings, filterable by conference |
| `get_team_info` | Team metadata (conference, division, abbreviation) |

To add a new tool: define its JSON schema in `TOOL_DEFINITIONS` in `tools.py`, add a handler branch in `execute_tool()`, and implement the data fetch in `nba_api.py`.

## Key concepts

**Why does `agent.py` loop?**
The Claude API is stateless — each call is independent. The loop re-sends the full conversation history (including tool results) on every iteration until Claude returns `stop_reason == "end_turn"`. A `max_iterations` guard prevents runaway loops.

**Why pass the full conversation history every call?**
Claude has no built-in memory. Conversation state lives in the `messages` list in `main.py` (or Streamlit's `session_state`), and is passed in full to every `client.messages.create()` call.

**Why does `tools.py` return JSON strings instead of dicts?**
The Claude API expects tool results as text content. `json.dumps()` converts Python dicts into strings Claude can read and reason about.
