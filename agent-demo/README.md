# Order Support Agent

A small but real LLM tool-calling agent: a FastAPI service that answers customer
questions about orders, looking up real data from MongoDB and calculating refunds
on request — deciding for itself when to call which tool, using Groq's
OpenAI-compatible function-calling API. No agent framework (no LangChain) — the
tool-calling loop in `agent.py` is written by hand so you can explain exactly how
it works in an interview.

## How it works

1. `tools.py` defines two tools as plain Python functions, plus a JSON-schema
   description of each (the format every major LLM provider's function-calling
   API expects).
2. `agent.py` sends the conversation + tool schemas to the model. If the model
   responds with a `tool_calls` request instead of plain text, the code runs the
   matching Python function, feeds the result back as a `tool` message, and asks
   the model again — looping until it gets a plain text answer.
3. `db.py` / `main.py` wire this into a FastAPI `/chat` endpoint, with MongoDB
   storing both the order data the tools query and the conversation history, so
   follow-up questions ("how much would a refund be?") have context.

## Run it locally

1. Get a free Groq API key: https://console.groq.com/keys
2. Copy `.env.example` to `.env` and fill in `GROQ_API_KEY`.
3. With Docker:
   ```
   docker compose up --build
   ```
4. Without Docker (needs a local MongoDB running on 27017):
   ```
   pip install -r requirements.txt
   export $(cat .env | xargs)
   uvicorn main:app --reload
   ```
5. In another terminal, run the test script:
   ```
   python test_agent.py
   ```
   You should see the agent look up ORD1001's real status, then calculate a
   refund using that order's actual amount — proof the tool calls are real,
   not scripted text.

## Talking about this in an interview

- "I built a hand-rolled tool-calling loop against Groq's function-calling API,
  not a framework, so I understand the underlying mechanism: schema → model
  decides to call a tool → I run the Python function → feed the result back →
  model continues."
- "Order lookups and refund math are backed by real MongoDB data, and
  conversation history persists per session so follow-up questions work."
- "It's intentionally small — two tools — because the point was proving I
  understand the tool-calling contract end-to-end, not building a large demo."
- A natural next step to mention: adding a third tool that calls a real external
  API (e.g. a shipping-carrier tracking API) to show multi-source tool use.
