import os
import asyncio
import logging
import threading
import time
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import Conflict, NetworkError, TimedOut

import ai
import tools
import voice as vc

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
bot_available = bool(TELEGRAM_BOT_TOKEN)

logger = logging.getLogger(__name__)

async def start(update: Update, context):
    await update.message.reply_text(
        "Good day, Sir. I am J.A.R.V.I.S. \u2014 Just A Rather Very Intelligent System.\n\n"
        "I am at your disposal for weather updates, news briefings, web searches, system monitoring, and general conversation.\n\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context):
    await update.message.reply_text(
        "Available commands, Sir:\n\n"
        "/start \u2014 Initialize our conversation\n"
        "/help \u2014 Display this message\n"
        "/weather [city] \u2014 Get current weather\n"
        "/news [topic] \u2014 Get top headlines\n"
        "/search [query] \u2014 Search the web\n"
        "/stats \u2014 System CPU, RAM, disk, battery\n\n"
        "You may also send me any message for general conversation, or a voice note for transcription and response."
    )

async def weather(update: Update, context):
    city = " ".join(context.args) if context.args else "London"
    try:
        data = tools.get_weather(city)
        if "error" in data:
            await update.message.reply_text(f"I apologize, Sir, but I could not fetch the weather. {data['error']}")
            return
        await update.message.reply_text(
            f"Weather in {data['city']}, {data['country']}: {data['description']}.\n"
            f"Temperature: {data['temp']}\u00b0C (feels like {data['feels_like']}\u00b0C).\n"
            f"Humidity: {data['humidity']}%, Wind: {data['wind_speed']} m/s."
        )
    except Exception:
        logger.exception("Weather command failed")
        await update.message.reply_text("I apologize, Sir, but I encountered an error fetching the weather.")

async def news(update: Update, context):
    topic = " ".join(context.args) if context.args else "general"
    try:
        articles = tools.get_news(topic)
        if isinstance(articles, dict) and "error" in articles:
            await update.message.reply_text(f"News unavailable: {articles['error']}")
            return
        if not articles:
            await update.message.reply_text("No news articles found, Sir.")
            return
        lines = [f"{i+1}. {a['title']} \u2014 {a['source']}" for i, a in enumerate(articles[:5])]
        await update.message.reply_text("Here are the top headlines, Sir:\n" + "\n".join(lines))
    except Exception:
        logger.exception("News command failed")
        await update.message.reply_text("I apologize, Sir, but I encountered an error fetching the news.")

async def search(update: Update, context):
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Please provide a search query, Sir.")
        return
    try:
        results = tools.web_search(query)
        if isinstance(results, list) and results:
            lines = [f"{i+1}. {r['title']}: {r.get('snippet', '')[:200]}" for i, r in enumerate(results[:3])]
            await update.message.reply_text(f"Search results for '{query}', Sir:\n" + "\n".join(lines))
        else:
            await update.message.reply_text(f"No results found for '{query}', Sir.")
    except Exception:
        logger.exception("Search command failed")
        await update.message.reply_text("I apologize, Sir, but I encountered an error with the web search.")

async def stats(update: Update, context):
    try:
        s = tools.get_system_stats()
        msg = (
            f"System status, Sir \u2014\n"
            f"CPU: {s['cpu']}%\n"
            f"RAM: {s['ram']}% ({s['ram_used_gb']}/{s['ram_total_gb']} GB)\n"
            f"Disk: {s['disk']}%"
        )
        if s.get("battery") is not None:
            msg += f"\nBattery: {s['battery']}%"
        await update.message.reply_text(msg)
    except Exception:
        logger.exception("Stats command failed")
        await update.message.reply_text("I apologize, Sir, but I encountered an error retrieving system stats.")

async def handle_text(update: Update, context):
    user_msg = update.message.text
    chat_id = str(update.effective_chat.id)
    try:
        full_response = ""
        async for token in ai.generate_stream(chat_id, user_msg):
            full_response += token
        await update.message.reply_text(full_response if full_response else "I apologize, Sir, but I encountered an error.")
    except Exception:
        logger.exception("Text handler failed")
        await update.message.reply_text("I apologize, Sir, but I encountered an error.")

async def handle_voice(update: Update, context):
    try:
        voice_file = await update.message.voice.get_file()
        ogg_bytes = await voice_file.download_as_bytearray()
        text = vc.speech_to_text(bytes(ogg_bytes))
        if not text:
            await update.message.reply_text("I could not understand the audio, Sir.")
            return
        chat_id = str(update.effective_chat.id)
        full_response = ""
        async for token in ai.generate_stream(chat_id, text):
            full_response += token
        await update.message.reply_text(full_response if full_response else "I apologize, Sir, but I encountered an error.")
    except Exception:
        logger.exception("Voice handler failed")
        await update.message.reply_text("I apologize, Sir, but I encountered an error processing your voice message.")

async def error_handler(update, context):
    if isinstance(context.error, Conflict):
        logger.warning("Telegram bot conflict detected (another instance running). Stopping bot.")
        await context.application.stop()
    elif isinstance(context.error, (NetworkError, TimedOut)):
        logger.warning(f"Telegram network error: {context.error}")
    else:
        logger.error(f"Telegram bot error: {context.error}")

async def post_init(app: Application):
    commands = [
        BotCommand("start", "Start J.A.R.V.I.S."),
        BotCommand("help", "Show available commands"),
        BotCommand("weather", "Get weather for a city"),
        BotCommand("news", "Get news headlines on a topic"),
        BotCommand("search", "Search the web"),
        BotCommand("stats", "Display system CPU, RAM, disk, battery"),
    ]
    try:
        await app.bot.set_my_commands(commands)
    except Exception as e:
        logger.warning(f"Failed to set bot commands: {e}")

def run_bot():
    if not bot_available:
        logger.warning("TELEGRAM_BOT_TOKEN not set. Telegram bot disabled.")
        return
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
        app.add_error_handler(error_handler)
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("weather", weather))
        app.add_handler(CommandHandler("news", news))
        app.add_handler(CommandHandler("search", search))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        logger.info("Starting J.A.R.V.I.S. Telegram bot...")
        app.run_polling(stop_signals=None)
    except Conflict:
        logger.warning("Telegram bot conflict — another instance is already running.")
    except Exception as e:
        logger.warning(f"Telegram bot failed to start: {e}")

def setup_bot(app):
    if not bot_available:
        logger.warning("TELEGRAM_BOT_TOKEN not set. Telegram bot disabled.")
        return
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    logger.info("Telegram bot thread started.")
