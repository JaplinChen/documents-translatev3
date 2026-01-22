
import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "translategemma:4b")

print(f"DEBUG: URL={OLLAMA_BASE_URL}, MODEL={OLLAMA_MODEL}")

async def run_debug_test():
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": "Hello, how are you?",
        "stream": False
    }
    
    print(f"\n--- Testing Generation ({url}) ---")
    try:
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            resp = await client.post(url, json=payload)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("Success! Model response available.")
                data = resp.json()
                print(f"Response snippet: {data.get('response', '')[:50]}...")
            else:
                print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Generation Failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(run_debug_test())
