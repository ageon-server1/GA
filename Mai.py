import os
import requests
import logging
from dotenv import load_dotenv
from telethon import TelegramClient, events

# 🔹 Load Environment Variables
load_dotenv()

API_ID = os.getenv("23227192")
API_HASH = os.getenv("7c3b59c3bb3429025f76b6840c7b7bf0")
BOT_TOKEN = os.getenv("7450391744:AAEb__pEdwLYY4zfb7F8WZPDs12XswyEUD8")
MISTRAL_API_KEY = os.getenv("YvKzfNvBoioL4aKaHn222FNyaWckgI0O")

bot = TelegramClient("mistral_ai_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Function: Call Mistral AI API
def chat_with_mistral(prompt):
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    data = {"model": "mistral-large", "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Mistral API: {e}")
        return "❌ AI Response Failed!"

# ✅ AI Chat Handler
@bot.on(events.NewMessage)
async def chat(event):
    user_input = event.text
    if not user_input.startswith("/"):
        await event.reply("🧠 Thinking...")
        response = chat_with_mistral(user_input)
        await event.reply(response)

# ✅ Summarization Feature
@bot.on(events.NewMessage(pattern="/summarize (.+)"))
async def summarize(event):
    text = event.pattern_match.group(1)
    prompt = f"Summarize this text in simple words:\n\n{text}"
    response = chat_with_mistral(prompt)
    await event.reply(response)

# ✅ AI Translation Feature
@bot.on(events.NewMessage(pattern="/translate (.+)"))
async def translate(event):
    text = event.pattern_match.group(1)
    prompt = f"Translate this text into English:\n\n{text}"
    response = chat_with_mistral(prompt)
    await event.reply(response)

# ✅ AI Paraphrasing Feature
@bot.on(events.NewMessage(pattern="/paraphrase (.+)"))
async def paraphrase(event):
    text = event.pattern_match.group(1)
    prompt = f"Rephrase the following text to make it unique and engaging:\n\n{text}"
    response = chat_with_mistral(prompt)
    await event.reply(response)

# ✅ AI Code Generation Feature
@bot.on(events.NewMessage(pattern="/code (.+)"))
async def code(event):
    query = event.pattern_match.group(1)
    prompt = f"Generate optimized and error-free code for: {query}"
    response = chat_with_mistral(prompt)
    await event.reply(f"🖥️ **Generated Code:**\n```python\n{response}```")

# ✅ AI Joke Generator
@bot.on(events.NewMessage(pattern="/joke"))
async def joke(event):
    prompt = "Tell me a funny joke."
    response = chat_with_mistral(prompt)
    await event.reply(f"😂 **Joke:**\n{response}")

# ✅ AI Fun Facts Generator
@bot.on(events.NewMessage(pattern="/fact"))
async def fun_fact(event):
    prompt = "Tell me an interesting fun fact."
    response = chat_with_mistral(prompt)
    await event.reply(f"🤯 **Did You Know?**\n{response}")

# ✅ AI Blog & Article Generator
@bot.on(events.NewMessage(pattern="/blog (.+)"))
async def blog(event):
    topic = event.pattern_match.group(1)
    prompt = f"Write a detailed and engaging blog post about: {topic}"
    response = chat_with_mistral(prompt)
    await event.reply(response)

# ✅ Bot Start Message
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.reply("🚀 **AGEON AI Bot Activated!**\n\nSend me any message and I will respond using **AGEON AI**.")

# ✅ Help Message
@bot.on(events.NewMessage(pattern="/help"))
async def help(event):
    help_text = """
🔹 **Available Commands:**
- `/ask <message>` – Get AI-generated response.
- `/summarize <text>` – Summarize a long paragraph.
- `/translate <text>` – Translate to English.
- `/paraphrase <text>` – Rephrase the given text.
- `/code <query>` – Generate AI-powered code.
- `/joke` – Get a random joke.
- `/fact` – Get an interesting fun fact.
- `/blog <topic>` – Generate an AI-powered blog post.
- `/info` – Get bot information.

✨ Send any text to chat with AI!
"""
    await event.reply(help_text)

# ✅ Bot Information
@bot.on(events.NewMessage(pattern="/info"))
async def info(event):
    bot_info = """
🤖 **AGEON AI Telegram Bot**
🔹 AI Model: **Mistral Large**
🔹 Features: Chat, Content Generation, Code Assistance, Summarization, Translation, Jokes, Fun Facts
🔹 Developer: @AGEON_OWNER
"""
    await event.reply(bot_info)

# ✅ Start the Bot
print("🚀 AGEON AI Telegram Bot is running...")
bot.run_until_disconnected()
