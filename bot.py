import discord
from discord.ext import commands, tasks
import os
import requests
import json
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv
import re

load_dotenv()

# =====================================================================
# CONFIG
# =====================================================================

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))

# YOUR FINAL DOMAINS
EMBED_SERVER_URL = "https://embed.ahazek.org/"
CDN_PROXY = "https://cdn.ahazek.org/get?url="

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

POSTED_TWEETS_FILE = "posted_tweets.json"


# =====================================================================
# HELPERS
# =====================================================================

def load_posted():
    if Path(POSTED_TWEETS_FILE).exists():
        try:
            return json.load(open(POSTED_TWEETS_FILE))
        except:
            return {}
    return {}

def save_posted(data):
    json.dump(data, open(POSTED_TWEETS_FILE, "w"), indent=2)


# =====================================================================
# FXTWITTER FUNCTIONS
# =====================================================================

def fetch_user_tweets(username):
    """Get latest tweets from FXTwitter."""
    url = f"https://api.fxtwitter.com/user/{username}"
    print("FETCH LATEST:", url)

    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        print("USER FETCH ERROR:", r.status_code)
        return []

    data = r.json()
    tweets = []

    for t in data.get("tweets", [])[:5]:
        media = []
        for m in t.get("media", []):
            media.append({
                "type": m.get("type"),
                "url": m.get("url"),
                "preview": m.get("thumbnail_url"),
                "video": m.get("url") if m.get("type") in ["video", "gif"] else None
            })

        tweets.append({
            "id": str(t["id"]),
            "text": t.get("text", ""),
            "url": t.get("url"),
            "metrics": t.get("stats", {}),
            "media": media
        })

    return tweets


def fetch_tweet_by_id(tweet_id):
    """Look up a single tweet directly."""
    url = f"https://api.fxtwitter.com/status/{tweet_id}"
    print("FETCHING:", url)

    r = requests.get(url, timeout=10)
    print("STATUS:", r.status_code)

    if r.status_code != 200:
        print("FX ERROR:", r.text)
        return None

    data = r.json().get("tweet")
    if not data:
        print("NO TWEET FIELD IN RESPONSE")
        return None

    print("TWEET FETCH SUCCESS")
    return data


# =====================================================================
# AUTO POSTING
# =====================================================================

async def send_tweet(tweet, channel, posted, force=False):
    if not force and tweet["id"] in posted:
        return

    image = None
    video = None

    for m in tweet.get("media", []):
        if m["type"] == "photo":
            image = m.get("url")
        elif m["type"] in ["video", "animated_gif", "gif"]:
            raw = m.get("url")
            if raw:
                video = CDN_PROXY + quote(raw, safe="")
            image = m.get("preview", image)

    embed = discord.Embed(description=tweet["text"], color=0x1DA1F2)

    embed.set_author(
        name="NFL (@NFL)",
        url=tweet["url"],
        icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
    )

    stats = tweet.get("metrics", {})
    embed.add_field(name="💬", value=stats.get("replies", 0))
    embed.add_field(name="🔁", value=stats.get("retweets", 0))
    embed.add_field(name="❤️", value=stats.get("likes", 0))
    embed.add_field(name="👁", value=stats.get("views", 0))

    if image:
        embed.set_image(url=image)

    await channel.send(embed=embed)

    # send video below (auto mode)
    if video:
        await channel.send(video)

    posted[tweet["id"]] = True
    save_posted(posted)


# =====================================================================
# STARTUP
# =====================================================================

async def startup():
    await bot.wait_until_ready()
    ch = bot.get_channel(DISCORD_CHANNEL_ID)
    if not ch:
        print("CHANNEL NOT FOUND")
        return

    tweets = fetch_user_tweets("NFL")
    posted = load_posted()

    for t in tweets[:2]:
        await send_tweet(t, ch, posted, force=True)

    save_posted(posted)


@bot.event
async def on_ready():
    print("Logged in as:", bot.user)
    bot.loop.create_task(startup())
    tweet_loop.start()


@tasks.loop(minutes=1)
async def tweet_loop():
    ch = bot.get_channel(DISCORD_CHANNEL_ID)
    posted = load_posted()
    tweets = fetch_user_tweets("NFL")

    for t in tweets:
        await send_tweet(t, ch, posted)

    save_posted(posted)


# =====================================================================
# !tweet (FULL FIXTWEET MODE)
# =====================================================================

TWEET_URL_REGEX = r"(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)"

@bot.command()
async def tweet(ctx, url: str):
    match = re.search(TWEET_URL_REGEX, url)
    if not match:
        return await ctx.send("❌ Invalid link.")

    username = match.group(1)
    tweet_id = match.group(2)

    print("USERNAME EXTRACTED:", username)
    print("LOOKUP TWEET ID:", tweet_id)

    tweet = fetch_tweet_by_id(tweet_id)
    if not tweet:
        return await ctx.send("❌ Could not fetch tweet.")

    text = tweet.get("text", "")
    stats = tweet.get("stats", {})

    # media
    image = None
    video = None

    for m in tweet.get("media", []):
        if m["type"] == "photo":
            image = m["url"]
        elif m["type"] in ["video", "animated_gif", "gif"]:
            raw = m.get("url")
            if raw:
                video = CDN_PROXY + quote(raw, safe="")
            image = m.get("thumbnail_url", image)

    # build embed server URL
    embed_url = (
        f"{EMBED_SERVER_URL}"
        f"?title=@{username}"
        f"&name={username}"
        f"&handle={username}"
        f"&text={quote(text)}"
        f"&likes={stats.get('likes', 0)}"
        f"&retweets={stats.get('retweets', 0)}"
        f"&replies={stats.get('replies', 0)}"
        f"&views={stats.get('views', 0)}"
    )

    if image:
        embed_url += "&image=" + quote(image)

    if video:
        embed_url += "&video=" + quote(video)

    print("EMBED_URL:", embed_url)

    await ctx.send(embed_url)


bot.run(DISCORD_TOKEN)
