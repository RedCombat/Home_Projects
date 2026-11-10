import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import requests

load_dotenv()

app = FastAPI()

# Fetches the URL from your local .env file
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_free_alert(text_content):
    # This formats a beautiful embed box in Discord
    payload = {
        "embeds": [
            {
                "title": "🚨 New Web Lead Intercepted",
                "description": text_content,
                "color": 5814783  # A nice blue accent color
            }
        ]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print(" Notification successfully pushed to your phone!")
        else:
            print(f" Discord responded with status: {response.status_code}")
    except Exception as e:
        print(f" Failed to route webhook alert: {e}")

@app.post("/webhook")
async def handle_incoming_lead(request: Request):
    # 1. Intercept data payload from your test URL
    payload = await request.json()
    name = payload.get("name", "Unknown")
    phone = payload.get("phone", "No Phone Provided")
    message = payload.get("message", "")
    
    # 2. Structure strict instructions for Gemma 4 running on your GPU
    prompt = f"""INSTRUCTIONS:
You are a precise data extraction tool for a local mobile service business. Analyze the incoming website message. Extract only the sender's Name, Phone Number, and provide a clear 1-sentence summary of their specific request. Do not include greetings, introductions, or conversational filler. Return the result strictly in this format:
Name: [Name] | Phone: [Phone] | Request: [Summary]

DATA TO ANALYZE:
Name: {name}
Phone: {phone}
Message: {message}"""

    print("\n Sending payload to local Gemma 4 model...")
    
    # 3. Post text to Ollama running on your GPU
    try:
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4:e4b",
                "prompt": prompt,
                "stream": False
            }
        ).json()
        
        ai_extraction = ollama_response.get("response", "").strip()
        print(f" AI Output: {ai_extraction}")
        
        # 4. Trigger the Discord notification
        send_free_alert(ai_extraction)
        
    except Exception as e:
        print(f" Error communicating with local Ollama: {e}")
    
    return {"status": "success", "engine": "local_hardware"}