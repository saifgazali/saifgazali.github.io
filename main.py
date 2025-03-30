import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
import httpx
from datetime import datetime

# --- LOAD FROM ENVIRONMENT ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_TABLE = "chat_logs"

# --- MISTRAL SETUP ---
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
model = "mistral-small-latest"

# --- FASTAPI APP SETUP ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SAVE CHAT TO SUPABASE ---
async def save_chat_to_supabase(user_id: str, message: str, reply: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
            headers={
                "apikey": SUPABASE_API_KEY,
                "Authorization": f"Bearer {SUPABASE_API_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            json={
                "user_id": user_id,
                "message": message,
                "reply": reply
            }
        )
        res.raise_for_status()

# --- ROUTES ---
@app.get("/")
def root():
    return {"message": "Mistral Chatbot backend with Supabase is running!"}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data["message"]
    user_id = data.get("user_id", "guest")

    response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": message}]
    )

    reply = response.choices[0].message.content
    await save_chat_to_supabase(user_id, message, reply)

    return {"reply": reply}
