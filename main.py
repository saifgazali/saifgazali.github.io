from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
from datetime import datetime
import httpx
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file if present

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Mistral Config ===
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
model = "mistral-small-latest"

# === Supabase Config ===
SUPABASE_API_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_TABLE = "chat_logs"

async def save_chat_to_supabase(user_id: str, message: str, reply: str):
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = {
        "user_id": user_id,
        "message": message,
        "reply": reply,
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        res = await httpx.post(
            f"{SUPABASE_API_URL}/rest/v1/{SUPABASE_TABLE}",
            headers=headers,
            json=data
        )
        res.raise_for_status()
    except httpx.HTTPStatusError as e:
        print("❌ Supabase saving error:", e)

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

    await save_chat_to_supabase(user_id, message, reply)

    return {"reply": reply}

@app.get("/")
def root():
    return {"message": "Mistral Chatbot backend is running!"}
