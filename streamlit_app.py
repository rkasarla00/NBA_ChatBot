"""
streamlit_app.py  —  Web UI for NBA ChatBot
--------------------------------------------
A clean chat interface using Streamlit.

Run it:
  streamlit run streamlit_app.py
"""

import streamlit as st
from agent import run_agent

# Page configuration
st.set_page_config(
    page_title="NBA Game Analyst",
    page_icon="🏀",
    layout="centered",
)

# Header
st.title("🏀 NBA Game Analyst")
st.caption("Ask me anything about players, teams, and standings.")

# Initialize conversation history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    # Only display user and assistant text messages
    if role in ("user", "assistant") and isinstance(content, str):
        with st.chat_message(role):
            st.markdown(content)

# Chat input
if prompt := st.chat_input("Ask about NBA players, teams, or standings..."):
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            # Pass a copy of messages - the agent mutates the list during tool calls
            messages_copy = [msg.copy() for msg in st.session_state.messages]
            response = run_agent(messages_copy)
        st.markdown(response)

    # Add assistant response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
    })

# Sidebar with info and clear button
with st.sidebar:
    st.header("About")
    st.markdown("""
    This chatbot uses **Claude** and the **balldontlie API**
    to answer questions about NBA basketball.

    **Try asking:**
    - "How is LeBron doing this season?"
    - "Show me the Lakers' recent games"
    - "What are the Western Conference standings?"
    - "Compare Steph Curry and Kevin Durant"
    """)

    st.divider()

    if st.button("Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Built with Streamlit + Claude + balldontlie API")
