# NBA Game Analyst Chatbot — Week 1

## Project structure

```
nba_analyst/
├── .env                  # Your secret API keys (never commit this)
├── requirements.txt      # Python packages to install
├── nba_api.py            # Layer 4: talks to balldontlie.io
├── tools.py              # Layer 3: wraps API calls as Claude tools
├── agent.py              # Layer 2: the Claude agent loop
└── main.py               # Layer 1: run the chatbot in your terminal
```

## Setup (do this once)

1. Install Python 3.9+ if you haven't already
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate      # Mac/Linux
   venv\Scripts\activate         # Windows
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your keys:
   - ANTHROPIC_API_KEY  → https://console.anthropic.com
   - BALLDONTLIE_API_KEY → https://www.balldontlie.io (free signup)

5. Run it:
   ```
   python main.py
   ```