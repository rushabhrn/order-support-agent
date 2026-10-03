"""Tools the agent can call. Each tool is a plain Python function plus a JSON-schema
spec in OpenAI/Groq 'tools' format, which is how real tool-calling / function-calling
works: the LLM sees the schema, decides a tool is needed, and returns a structured
tool_call instead of (or before) a text answer."""
from db import orders_col


def get_order_status(order_id: str) -> dict:
    """Look up a single order's status, item, and delivery estimate from MongoDB."""
    order = orders_col.find_one({"order_id": order_id.upper()}, {"_id": 0})
    if not order:
        return {"error": f"No order found with ID {order_id}"}
    return {
        "order_id": order["order_id"],
        "item": order["item"],
        "status": order["status"],
        "amount": order["amount"],
        "expected_delivery": order["expected_delivery"].strftime("%Y-%m-%d"),
    }


def calculate_refund(amount: float, refund_percentage: float) -> dict:
    """Calculate a refund amount given the original order amount and a refund percentage."""
    refund = round(amount * (refund_percentage / 100), 2)
    return {
        "original_amount": amount,
        "refund_percentage": refund_percentage,
        "refund_amount": refund,
    }


# JSON-schema tool specs in the format Groq/OpenAI chat-completions expects.
TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Get the current status, item, amount, and expected delivery date for a customer's order, given the order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID, e.g. ORD1001",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_refund",
            "description": "Calculate the refund amount for an order given its total amount and the refund percentage to apply.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Original order amount"},
                    "refund_percentage": {
                        "type": "number",
                        "description": "Percentage of the amount to refund, e.g. 50 for a 50% refund",
                    },
                },
                "required": ["amount", "refund_percentage"],
            },
        },
    },
]

# Maps tool name -> actual Python callable, so the agent loop can dispatch calls.
TOOL_REGISTRY = {
    "get_order_status": get_order_status,
    "calculate_refund": calculate_refund,
}
