import discord
from discord.ext import commands, tasks
import os
import requests
import json
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv
import re

# ============================================================
# LOAD ENV + DEBUG
# ============================================================

load_dotenv()

print("=== TOKEN DEBUG ===")
print("TOKEN:", os.getenv("TWITTER_BEARER_TOKEN"))
print("LENGTH:", len(os.getenv("TWITTER_BEARER_TOKEN") or "NONE"))
print("===================")

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))

# YOUR SERVICES
EMBED_SERVER_URL = "https://ridiculous-cindra-oknonononon-1d15a38f.koyeb.app/"
CDN_PROXY = "https://cdn.ahazek.org/get?url="

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# DISCORD BOT
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

POSTED_TWEETS_FILE = "posted_tweets.json"


# ============================================================
# LOAD / SAVE POSTED TWEETS
# ============================================================

def load_posted():
    if Path(POSTED_TWEETS_FILE).exists():
        try:
            return json.load(open(POSTED_TWEETS_FILE))
        except:
            return {}
    return {}

def save_posted(data):
    json.dump(data, open(POSTED_TWEETS_FILE, "w"), indent=2)


# ============================================================
# FETCH TWEET BY ID (VXTwitter — ALWAYS works)
# ============================================================

def get_tweet_by_id(tweet_id):
    """
    Fetch one tweet using VXTwitter's tweet-by-ID API.
    This ALWAYS works, even for large accounts.
    """
    try:
        print("Fetching TWEET via VX:", tweet_id)

        r = requests.get(
            f"https://api.vxtwitter.com/{tweet_id}",
            timeout=10,
            headers=HEADERS
        )

        print("VX TWEET STATUS:", r.status_code)

        if r.status_code != 200:
            print("VX ERROR:", r.text)
            return None

        data = r.json()

        media_list = []
        for m in data.get("media", []):
            media_list.append({
                "type": m.get("type"),
                "url": m.get("url"),
                "preview_image_url": m.get("thumbnail_url"),
                "video_url": m.get("url") if m.get("type") in ["video", "gif"] else None
            })

        tweet = {
            "id": str(data["tweet"]["id"]),
            "text": data["tweet"]["text"],
            "url": data["tweet"]["url"],
            "metrics": data["tweet"].get("stats", {}),
            "media": media_list
        }

        print("VX FETCHED:", tweet["id"])
        return tweet

    except Exception as e:
        print("VX CRASH:", e)
        return None


# ============================================================
# AUTO POST TWEET (Top 2 every restart + new ones)
# ============================================================

async def send_tweet(tweet, channel, posted, force=False):

    if not force and tweet["id"] in posted:
        return

    image_url = None
    video_url = None

    for m in tweet.get("media", []):
        if m["type"] == "photo":
            image_url = m["url"]
        elif m["type"] in ["video", "animated_gif", "gif"]:
            raw = m.get("video_url")
            video_url = CDN_PROXY + quote(raw, safe="")
            image_url = m.get("preview_image_url", image_url)

    # BASIC embed for auto-poster
    embed = discord.Embed(description=tweet["text"], color=0x1DA1F2)
    embed.set_author(
        name="NFL (@NFL)",
        url=tweet["url"],
        icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
    )

    stats = tweet["metrics"]
    embed.add_field(name="💬", value=stats.get("reply_count", 0))
    embed.add_field(name="🔁", value=stats.get("retweet_count", 0))
    embed.add_field(name="❤️", value=stats.get("like_count", 0))
    embed.add_field(name="👁", value=stats.get("view_count", 0))

    if image_url:
        embed.set_image(url=image_url)

    await channel.send(embed=embed)

    # send video below
    if video_url:
        await channel.send(video_url)

    posted[tweet["id"]] = True
    save_posted(posted)


# ============================================================
# STARTUP
# ============================================================

async def startup():
    await bot.wait_until_ready()

    ch = bot.get_channel(DISCORD_CHANNEL_ID)
    if not ch:
        print("Channel not found")
        return

    posted = load_posted()

    # Fetch NFL latest tweet via ID isn't possible — so skip
    # Just ensure bot runs
    print("Startup completed.")


@bot.event
async def on_ready():
    print("Logged in as:", bot.user)
    bot.loop.create_task(startup())


# ============================================================
# !tweet — FULL FIXTWEET-STYLE EMBED
# ============================================================

TWEET_URL_REGEX = r"(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)"

@bot.command()
async def tweet(ctx, url: str):
    match = re.search(TWEET_URL_REGEX, url)
    if not match:
        return await ctx.send("❌ Invalid link.")

    username = match.group(1)
    tweet_id = match.group(2)

    print("USERNAME:", username)
    print("TWEET ID:", tweet_id)

    # Fetch tweet by ID (always works)
    target = get_tweet_by_id(tweet_id)

    if not target:
        return await ctx.send("❌ Could not fetch tweet.")

    image_url = None
    video_url = None

    for m in target.get("media", []):
        if m["type"] == "photo":
            image_url = m["url"]
        elif m["type"] in ["video", "animated_gif", "gif"]:
            raw = m.get("video_url")
            video_url = CDN_PROXY + quote(raw, safe="")
            image_url = m.get("preview_image_url", image_url)

    # Build embed link
    embed_url = (
        f"{EMBED_SERVER_URL}"
        f"?title=@{username}"
        f"&name={username}"
        f"&handle={username}"
        f"&text={quote(target['text'])}"
        f"&likes={target['metrics'].get('like_count', 0)}"
        f"&retweets={target['metrics'].get('retweet_count', 0)}"
        f"&replies={target['metrics'].get('reply_count', 0)}"
        f"&views={target['metrics'].get('view_count', 0)}"
    )

    if image_url:
        embed_url += "&image=" + quote(image_url)

    if video_url:
        embed_url += "&video=" + quote(video_url)

    print("EMBED_URL:", embed_url)

    await ctx.send(embed_url)


# ============================================================
# RUN BOT
# ============================================================

bot.run(DISCORD_TOKEN)
