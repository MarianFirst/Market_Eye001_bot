
# market_news_bot.py
import os
import json
import requests
import feedparser
import matplotlib.pyplot as plt
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import requests
except ImportError:
    install("requests")

try:
    import feedparser
except ImportError:
    install("feedparser")


# === LOAD CONFIG ===
with open("telegram_bot_config.json", "r") as f:
    config = json.load(f)

BOT_TOKEN = config["BOT_TOKEN"]
TIMEZONE = pytz.timezone("Europe/London")  # Matches GMT+1 with DST
POST_TIMES = config["POST_TIMES"]
CHARTS_ENABLED = config["CHARTS_ENABLED"]

bot = Bot(token=BOT_TOKEN)
scheduler = BlockingScheduler(timezone=TIMEZONE)
CHAT_ID = None

GNEWS_API = "https://gnews.io/api/v4/top-headlines?category=business&lang=en&token=demo"
RSS_FEEDS = [
    "http://feeds.reuters.com/reuters/businessNews",
    "http://rss.cnn.com/rss/money_latest.rss"
]

def get_news():
    headlines = []
    try:
        r = requests.get(GNEWS_API)
        data = r.json()
        for article in data.get("articles", [])[:3]:
            headlines.append({
                "title": article['title'],
                "desc": article['description'],
                "source": article['source']['name'],
                "url": article['url']
            })
    except:
        pass

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:2]:
            headlines.append({
                "title": entry.title,
                "desc": entry.summary[:150],
                "source": entry.link.split("/")[2],
                "url": entry.link
            })

    return headlines[:5]

def make_chart():
    x = list(range(10))
    y = [val**1.5 for val in x]
    plt.figure()
    plt.plot(x, y)
    plt.title("Sample Market Trend")
    plt.xlabel("Day")
    plt.ylabel("Index")
    plt.savefig("chart.png")

def send_update():
    global CHAT_ID
    news_items = get_news()
    text = "\U0001F4F0 <b>Market Insights</b>\n\n"

    for item in news_items:
        text += f"<b>{item['title']}</b>\n"
        text += f"{item['desc']}\n"
        text += f"<i>Source: {item['source']}</i>\n"
        text += f"<a href='{item['url']}'>Read more</a>\n\n"

    if CHAT_ID:
        if CHARTS_ENABLED:
            make_chart()
            with open("chart.png", "rb") as f:
                bot.send_photo(chat_id=CHAT_ID, photo=f, caption="Market chart")
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML", disable_web_page_preview=True)

def register():
    updates = bot.get_updates()
    if updates:
        global CHAT_ID
        CHAT_ID = updates[-1].message.chat_id

for post_time in POST_TIMES:
    hour, minute = map(int, post_time.split(":"))
    scheduler.add_job(send_update, 'cron', hour=hour, minute=minute)

if __name__ == "__main__":
    register()
    print("Market_Eye001_bot is running...")
    scheduler.start()
