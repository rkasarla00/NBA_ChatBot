"""
main.py  —  Layer 1: Terminal chat interface
--------------------------------------------
The simplest possible UI — your terminal.
This keeps Week 1 focused on the AI plumbing,
not on frontend code. We add Streamlit in Week 3.

Run it:
  python main.py
"""

from agent import run_agent

def main():
    print("\n🏀  NBA Game Analyst  🏀")
    print("Ask me anything about players, teams, and standings.")
    print("Type 'quit' to exit.\n")

    # The conversation history — starts empty, grows with each turn.
    # WHY store this here?
    #   agent.py is stateless (it just takes messages and returns an answer).
    #   main.py is the only thing that persists across turns.
    #   This separation keeps each file focused on one job.
    conversation = []

    while True:
        # Get user input
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Later! 🏀")
            break

        # Add the user's message to history
        conversation.append({
            "role": "user",
            "content": user_input,
        })

        print("\nAnalyst: ", end="", flush=True)

        # Run the agent — it will loop internally until it has an answer
        answer = run_agent(conversation)
        print(answer)

        # Add Claude's answer to history so future turns have context
        conversation.append({
            "role": "assistant",
            "content": answer,
        })

        print()  # blank line between turns


if __name__ == "__main__":
    main()