"""FastAPI entrypoint for the Order Support Agent demo."""
from fastapi import FastAPI
from pydantic import BaseModel

from db import seed_orders, save_turn, get_history
from agent import run_agent

app = FastAPI(title="Order Support Agent")


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.on_event("startup")
def startup():
    seed_orders()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = get_history(req.session_id)
    reply = run_agent(req.message, history)

    save_turn(req.session_id, "user", req.message)
    save_turn(req.session_id, "assistant", reply)

    return ChatResponse(reply=reply)
