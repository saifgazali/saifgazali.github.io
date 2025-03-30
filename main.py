from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
from datetime import datetime
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))  # Store your key in Render env vars
model = "mistral-small-latest"

CHAT_HISTORY_FILE = "chat_history.json"

def save_chat(user_id, message, reply):
    timestamp = datetime.utcnow().isoformat()
    record = {"timestamp": timestamp, "user": user_id, "message": message, "reply": reply}

    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    history.append(record)

    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(history, f)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data["message"]
    user_id = data.get("user_id", "anonymous")

    response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": message}]
    )

    reply = response.choices[0].message.content
    save_chat(user_id, message, reply)

    return {"reply": reply}

@app.get("/")
def root():
    return {"message": "Mistral Chatbot backend is running!"}

@app.get("/history")
def get_history():
    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
