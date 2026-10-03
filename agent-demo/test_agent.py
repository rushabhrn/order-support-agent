"""Quick manual test: run this after `docker compose up` (or after running
MongoDB + uvicorn locally) to confirm the agent actually calls its tools.

    python test_agent.py
"""
import requests

BASE_URL = "http://localhost:8000"


def ask(session_id: str, message: str):
    resp = requests.post(f"{BASE_URL}/chat", json={"session_id": session_id, "message": message})
    resp.raise_for_status()
    print(f"\nYou: {message}")
    print(f"Agent: {resp.json()['reply']}")


if __name__ == "__main__":
    sid = "demo-session-1"
    # This should trigger get_order_status
    ask(sid, "What's the status of order ORD1001?")
    # This should trigger calculate_refund, using the amount from the order above
    ask(sid, "If I cancel it, how much would a 50% refund be?")
    # Plain conversation, no tool call expected
    ask(sid, "Thanks, that's all I needed.")
