from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from main import handle_chat

app = FastAPI()


class Message(BaseModel):
    role: str
    content: Any
    recommendations: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    messages: List[Message]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    messages = []

    for msg in request.messages:
        messages.append(
            {
                "role": msg.role,
                "content": msg.content,
                "recommendations": msg.recommendations,
            }
        )

    print(messages)  # remove later if needed

    response = handle_chat(messages)
    return response
