"""A minimal but real tool-calling agent loop against Groq's OpenAI-compatible
chat completions API. No framework (no LangChain) — this is the raw mechanism
agent frameworks wrap, written out so it's easy to explain in an interview:

1. Send the user's message + tool schemas to the LLM.
2. If the LLM responds with tool_calls, run the matching Python function(s)
   and feed the result back as a 'tool' message.
3. Repeat until the LLM returns a plain text answer (or a max-steps safety limit).
"""
import json
import os
import requests

from tools import TOOL_SPECS, TOOL_REGISTRY

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = (
    "You are a helpful customer support agent for an e-commerce company. "
    "Use the available tools to look up real order information or calculate "
    "refunds before answering. Never guess an order's status — always call "
    "get_order_status. Be concise and friendly."
)

MAX_STEPS = 5


def _call_groq(messages: list) -> dict:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_SPECS,
        "tool_choice": "auto",
        "temperature": 0.2,
    }
    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def run_agent(user_message: str, history: list) -> str:
    """Run the tool-calling loop for one user turn, given prior conversation history
    (list of {role, content} dicts pulled from MongoDB), and return the final reply."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_STEPS):
        result = _call_groq(messages)
        choice = result["choices"][0]
        msg = choice["message"]

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            return msg["content"]

        # The model asked for one or more tool calls — append its request, then
        # run each tool and append the result before looping back.
        messages.append(msg)
        for call in tool_calls:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"] or "{}")
            fn = TOOL_REGISTRY.get(name)
            output = fn(**args) if fn else {"error": f"Unknown tool {name}"}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(output),
                }
            )

    return "Sorry, I couldn't resolve that in time — could you rephrase your question?"
