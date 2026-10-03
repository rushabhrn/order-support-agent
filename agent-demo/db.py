"""MongoDB connection and seed data for the Order Support Agent demo."""
import os
from datetime import datetime, timedelta
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "order_agent")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

orders_col = db["orders"]
conversations_col = db["conversations"]


def seed_orders():
    """Populate a handful of sample orders so the agent's tools have real data to query."""
    if orders_col.count_documents({}) > 0:
        return
    sample_orders = [
        {
            "order_id": "ORD1001",
            "customer_name": "Asha Rao",
            "item": "Wireless Headphones",
            "amount": 2499.0,
            "status": "shipped",
            "placed_on": datetime.utcnow() - timedelta(days=3),
            "expected_delivery": datetime.utcnow() + timedelta(days=2),
        },
        {
            "order_id": "ORD1002",
            "customer_name": "Vikram Shah",
            "item": "Smartwatch",
            "amount": 5999.0,
            "status": "delivered",
            "placed_on": datetime.utcnow() - timedelta(days=10),
            "expected_delivery": datetime.utcnow() - timedelta(days=5),
        },
        {
            "order_id": "ORD1003",
            "customer_name": "Priya Nair",
            "item": "Bluetooth Speaker",
            "amount": 1899.0,
            "status": "processing",
            "placed_on": datetime.utcnow() - timedelta(hours=6),
            "expected_delivery": datetime.utcnow() + timedelta(days=5),
        },
    ]
    orders_col.insert_many(sample_orders)
    print(f"Seeded {len(sample_orders)} sample orders.")


def save_turn(session_id: str, role: str, content: str):
    """Append one conversation turn to MongoDB so history persists across requests."""
    conversations_col.update_one(
        {"session_id": session_id},
        {"$push": {"messages": {"role": role, "content": content, "ts": datetime.utcnow()}}},
        upsert=True,
    )


def get_history(session_id: str):
    doc = conversations_col.find_one({"session_id": session_id})
    if not doc:
        return []
    return [{"role": m["role"], "content": m["content"]} for m in doc.get("messages", [])]
