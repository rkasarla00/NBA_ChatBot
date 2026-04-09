"""
agent.py  —  Layer 2: The Claude agent loop
--------------------------------------------
This is the most important file to understand.
It implements the "agentic loop" — the back-and-forth
between Claude and your tools until Claude has a final answer.

THE LOOP (read this carefully):
  ┌─────────────────────────────────────────┐
  │  1. Send messages + tools to Claude     │
  │  2. Did Claude call a tool?             │
  │     YES → run the tool, add result,     │
  │            go back to step 1            │
  │     NO  → Claude gave a final answer,   │
  │            return it to the user        │
  └─────────────────────────────────────────┘

WHY loop?
  One question might need multiple tool calls.
  e.g. "Compare LeBron and Curry this season"
    → Claude calls get_player_stats("LeBron James")
    → gets result, then calls get_player_stats("Steph Curry")
    → gets result, then writes the comparison
  Each tool call is a separate round trip.
"""

import os
import anthropic
from dotenv import load_dotenv
from tools import TOOL_DEFINITIONS, execute_tool

load_dotenv()

# One client instance, reused for the whole session.
# WHY? Creating a new client per message is wasteful.
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert NBA analyst with access to live basketball data.
When a user asks about players, teams, games, or standings, use your tools to 
look up accurate data before answering. Always cite specific stats in your response.
Keep your tone like an engaged sports analyst — knowledgeable but conversational."""


def run_agent(messages: list) -> str:
    """
    The core agent loop. Takes a conversation history and returns Claude's final answer.

    'messages' is the full conversation so far:
      [
        {"role": "user",      "content": "How is LeBron doing?"},
        {"role": "assistant", "content": "..."},  # previous turns
        {"role": "user",      "content": "What about Curry?"},  # latest question
      ]

    WHY pass the full history?
      Claude has no memory between calls. Every call is stateless.
      You simulate memory by passing all previous messages every time.
      This is how all LLM conversation works under the hood.
    """

    # Safety valve — prevent runaway loops (e.g. if a tool keeps erroring)
    max_iterations = 10

    for iteration in range(max_iterations):

        # ── Step 1: Call Claude ──────────────────────────────────────────
        response = client.messages.create(
            model="claude-sonnet-4-6",          # Latest Sonnet — fast + smart
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,             # Claude can see these tools
            messages=messages,
        )

        # ── Step 2: Did Claude want to call a tool? ─────────────────────
        if response.stop_reason == "tool_use":
            # Claude returned one or more tool_use blocks.
            # We need to:
            #   a) Add Claude's response to message history
            #   b) Run each requested tool
            #   c) Add ALL tool results in a single user message
            #   d) Loop back to call Claude again

            # a) Add Claude's response (which contains the tool_use blocks)
            messages.append({
                "role": "assistant",
                "content": response.content,  # This is a list of content blocks
            })

            # b) & c) Run each tool and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [tool call] {block.name}({block.input})")  # visible in terminal
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,   # Must match the tool_use block's id
                        "content": result,
                    })

            # d) Send all results back in one user message, then loop
            messages.append({
                "role": "user",
                "content": tool_results,
            })

            # Continue the loop — Claude will read the results and either
            # call more tools or give its final answer.
            continue

        # ── Step 3: Claude gave a final answer ─────────────────────────
        # stop_reason == "end_turn" means no more tool calls needed.
        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return final_text

    # If we somehow hit max_iterations, return a safe fallback
    return "I hit the maximum number of steps. Please try rephrasing your question."