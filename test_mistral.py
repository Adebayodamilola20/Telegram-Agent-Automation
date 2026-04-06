import httpx, asyncio, json, os
from dotenv import load_dotenv

load_dotenv()

async def t():
    url = 'https://api.mistral.ai/v1/chat/completions'
    api_key = os.getenv('MISTRAL_API_KEY')
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    system_prompt = """You are Jarvis, a MacOS assistant acting through a Telegram bot. 
The user will send you natural language messages. You can respond in two ways:
1. Execute a command on the user's Mac.
2. Just chat with the user.
Always respond in purely valid JSON format without markdown wrapping. 
Structure:
{"type": "bash" | "applescript" | "chat", "command": "<command if applicable>", "reply": "<reply text>"}
"""
    data = {
        'model': 'mistral-large-latest',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': 'chat open whatsapp onn my laptop'}
        ],
        'response_format': {'type': 'json_object'}
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=data, headers=headers)
        print(response.text)

asyncio.run(t())
