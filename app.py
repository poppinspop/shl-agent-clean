from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from main import handle_chat  # assuming your logic file is main.py

app = FastAPI()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    response = handle_chat(messages)
    return response
