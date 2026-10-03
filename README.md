# Order Support Agent

A small but real LLM tool-calling agent: a FastAPI service that answers customer
questions about orders by deciding, on its own, when to look up real data in
MongoDB or calculate a refund — using Groq's OpenAI-compatible function-calling
API. No agent framework (no LangChain) — the tool-calling loop is hand-written
so the whole mechanism is visible and explainable end to end.

## Tech stack

| Layer            | Choice                                           |
|-------------------|---------------------------------------------------|
| API               | FastAPI + Uvicorn                                  |
| LLM / tool calling | Groq (`openai/gpt-oss-20b`), OpenAI-compatible function-calling API |
| Database          | MongoDB (order records + per-session conversation history) |
| Containerization   | Docker + Docker Compose (app + MongoDB)            |
| HTTP client        | `requests` (no SDK — raw API calls)               |

## Architecture

```
 User message
      │
      ▼
 FastAPI  /chat  ──────────────►  MongoDB (conversations)
      │                              ▲ save turn
      ▼                              │
 agent.run_agent()                   │
      │                              │
      ├─► Groq chat/completions  ◄───┘ (prior history + tool schemas)
      │        │
      │        ▼
      │   tool_calls? ──No──► return plain-text reply
      │        │
      │       Yes
      │        ▼
      │   run matching Python tool  ──►  MongoDB (orders)
      │        │
      │        ▼
      │   feed tool result back to Groq, loop
      ▼
   final reply
```

## How it works

1. **`tools.py`** defines two tools as plain Python functions, plus a JSON-schema
   description of each — the format every major LLM provider's function-calling
   API expects:
   - `get_order_status(order_id)` — looks up a real order in MongoDB.
   - `calculate_refund(amount, refund_percentage)` — computes a refund.
2. **`agent.py`** sends the conversation + tool schemas to the model. If the
   model responds with a `tool_calls` request instead of plain text, the code
   runs the matching Python function, feeds the result back as a `tool`
   message, and asks the model again — looping until it returns a plain text
   answer (capped at `MAX_STEPS` to avoid infinite loops).
3. **`db.py` / `main.py`** wire this into a FastAPI `/chat` endpoint. MongoDB
   stores both the order data the tools query and the conversation history per
   `session_id`, so follow-up questions ("how much would a refund be?") have
   context from the turn before.

## Example interaction

```
You: What's the status of order ORD1001?
→ agent calls get_order_status(order_id="ORD1001")
→ MongoDB returns: {item: "Wireless Headphones", status: "shipped", amount: 2499.0, ...}
Agent: Your order ORD1001 (Wireless Headphones) has shipped and is expected
       to arrive on [date]. Let me know if you need anything else!

You: If I cancel it, how much would a 50% refund be?
→ agent calls calculate_refund(amount=2499.0, refund_percentage=50)
Agent: A 50% refund on your ₹2,499 order would come to ₹1,249.50.
```

Both tool calls are real — the model decided to invoke them, and the numbers
come from actual MongoDB data and actual arithmetic, not scripted text.

## Run it locally

1. Get a free Groq API key: https://console.groq.com/keys
2. Copy `.env.example` to `.env` and fill in `GROQ_API_KEY` (no quotes around
   the value).
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
   refund using that order's actual amount.

## Project structure

```
agent-demo/
├── main.py           # FastAPI app and /chat endpoint
├── agent.py           # Hand-rolled tool-calling loop against Groq
├── tools.py            # Tool functions + their JSON-schema specs
├── db.py               # MongoDB connection, seed data, conversation history
├── test_agent.py        # Manual end-to-end test script
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Design notes / what I'd build next

- Intentionally small (two tools) — the point was proving I understand the
  tool-calling contract end-to-end, not building a large demo.
- No framework (no LangChain/LlamaIndex): the loop in `agent.py` is ~70 lines
  and makes the request/response contract explicit rather than hiding it
  behind an abstraction.
- Natural next steps: a third tool that calls a real external API (e.g. a
  shipping-carrier tracking API) to show multi-source tool use; streaming
  responses; retries/backoff on the Groq call; auth on the `/chat` endpoint.
