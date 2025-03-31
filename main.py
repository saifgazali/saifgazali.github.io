from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
from datetime import datetime
import httpx
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file if present

from fastapi import HTTPException

app = FastAPI()

# Dummy user database (for just 2 users)
users_db = {
    "saif": {
        "password": "1234",
        "uuid": "user-001"
    },
    "aiva": {
        "password": "5678",
        "uuid": "user-002"
    }
}

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    if username not in users_db or users_db[username]["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"uuid": users_db[username]["uuid"]}


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

import httpx

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
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{SUPABASE_API_URL}/rest/v1/{SUPABASE_TABLE}",
                headers=headers,
                json=data
            )
            res.raise_for_status()
    except httpx.HTTPStatusError as e:
        print("❌ Supabase saving error:", e)

async def get_last_5_chats(user_id):
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}"
    }

    params = {
        "user_id": f"eq.{user_id}",
        "order": "timestamp.desc",
        "limit": 5
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{SUPABASE_API_URL}/rest/v1/{SUPABASE_TABLE}",
                headers=headers,
                params=params
            )
            res.raise_for_status()
            return res.json()
    except Exception as e:
        print("⚠️ Error getting chat history:", e)
        return []


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data["message"]
    user_id = data.get("user_id", "anonymous")

    # 🧠 Step 1: Fetch last 5 message-reply pairs for the user
    context_msgs = await get_last_5_chats(user_id)

    # 🧠 Step 2: Format them as context
    formatted_context = []
    for item in context_msgs:
        formatted_context.append({"role": "user", "content": item["message"]})
        formatted_context.append({"role": "assistant", "content": item["reply"]})

    # 🧠 Step 3: Add current message at the end
    formatted_context.append({"role": "user", "content": f"{message}\n\n(Considérez ce qui précède comme contexte au cas où il s’agirait d’un suivi.)"})

    # 🤖 Step 4: Get reply from Mistral
    response = client.chat.complete(
        model=model,
        messages=formatted_context
    )
    reply = response.choices[0].message.content

    # 💾 Step 5: Save to Supabase
    await save_chat_to_supabase(user_id, message, reply)

    return {"reply": reply}


@app.get("/")
def root():
    return {"message": "Mistral Chatbot backend is running!"}
