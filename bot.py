import discord
from discord.ext import commands, tasks
import os
import json
import requests
import re
import asyncio
import random
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# ======================
# ENV / BOT SETUP
# ======================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# CONFIG
# ======================
USERNAME = "jiecia48"

NITTER_HTML_LIST = [
    f"https://nitter.net/{USERNAME}",
    f"https://nitter.poast.org/{USERNAME}",
    f"https://nitter.snopyta.org/{USERNAME}",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (DiscordBot HTML Fetcher)"
}

POSTED_FILE = "posted_tweets.json"

# ======================
# POSTED TWEETS UTILS
# ======================
def load_posted():
    if os.path.exists(POSTED_FILE):
        try:
            with open(POSTED_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_posted(ids):
    with open(POSTED_FILE, "w") as f:
        json.dump(ids[-100:], f, indent=2)

posted_tweets = load_posted()

# ======================
# HTML PARSER
# ======================
def get_tweets_from_html():
    for url in NITTER_HTML_LIST:
        try:
            print(f"🌐 Trying HTML: {url}")
            r = requests.get(url, headers=HEADERS, timeout=10)

            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            tweets = []

            for item in soup.select(".timeline-item")[:10]:
                link = item.select_one("a.tweet-link")
                if not link:
                    continue

                href = link.get("href", "")
                match = re.search(r"/status/(\d+)", href)
                if not match:
                    continue

                tweet_id = match.group(1)
                tweets.append(tweet_id)

            if tweets:
                print(f"✅ HTML tweets found: {tweets}")
                return tweets

        except Exception as e:
            print(f"❌ HTML error ({url}): {e}")

    print("🚨 All HTML sources failed")
    return []

# ======================
# EVENTS
# ======================
@bot.event
async def on_ready():
    print(f"✅ Bot logged in as: {bot.user}")
    print(f"📺 Channel ID: {DISCORD_CHANNEL_ID}")
    print(f"📝 Already posted: {len(posted_tweets)} tweets")
    tweet_loop.start()

# ======================
# MAIN LOOP
# ======================
@tasks.loop(minutes=2)
async def tweet_loop():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    print(f"🔗 Channel fetched: {channel}")

    if not channel:
        print("❌ Channel not found")
        return

    tweets = get_tweets_from_html()
    if not tweets:
        print("⚠️ No tweets found from HTML")
        return

    new_count = 0
    for tweet_id in tweets:
        if tweet_id in posted_tweets:
            continue

        url = f"https://fxtwitter.com/{USERNAME}/status/{tweet_id}"
        print(f"✉️ Sending tweet: {tweet_id}")
        await channel.send(url)

        posted_tweets.append(tweet_id)
        new_count += 1

    if new_count:
        save_posted(posted_tweets)
        print(f"📊 Posted {new_count} new tweet(s)")
    else:
        print("✓ No new tweets to post")

@tweet_loop.before_loop
async def before_loop():
    await bot.wait_until_ready()
    delay = random.randint(0, 10)
    print(f"⏱️ Initial delay: {delay}s")
    await asyncio.sleep(delay)

# ======================
# COMMANDS
# ======================
@bot.command()
async def tweet(ctx, url: str):
    match = re.search(r"(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)", url)
    if not match:
        return await ctx.send("❌ Invalid tweet URL")

    user, tweet_id = match.groups()
    fx = f"https://fxtwitter.com/{user}/status/{tweet_id}"

    try:
        await ctx.message.delete()
    except:
        pass

    await ctx.send(fx)

@bot.command()
async def status(ctx):
    await ctx.send(
        f"✅ **Bot Status**\n"
        f"📺 Channel: <#{DISCORD_CHANNEL_ID}>\n"
        f"📝 Tracked tweets: {len(posted_tweets)}\n"
        f"🔄 Loop running: {tweet_loop.is_running()}"
    )

@bot.command()
async def clear(ctx):
    global posted_tweets
    posted_tweets = []
    save_posted(posted_tweets)
    await ctx.send("🧹 Cleared tweet history")

# ======================
# RUN
# ======================
bot.run(DISCORD_TOKEN)            return

        print(f"📊 Found {len(tweets)} total tweets")
        print(f"📝 Already posted tweets: {posted_tweets}")

        new_count = 0
        for tweet in tweets:
            tweet_id = tweet['id']

            if tweet_id in posted_tweets:
                print(f"⏭ Skipping already posted tweet: {tweet_id}")
                continue

            url = f"https://fxtwitter.com/jiecia48/status/{tweet_id}"
            print(f"✉️ Sending tweet: {tweet_id} -> {url}")
            await channel.send(url)

            posted_tweets.append(tweet_id)
            new_count += 1

        if new_count > 0:
            save_posted(posted_tweets)
            print(f"📊 Posted {new_count} new tweet(s)")
        else:
            print("✓ No new tweets to post")

    except Exception as e:
        print(f"❌ Error in tweet loop: {e}")

@tweet_loop.before_loop
async def before_tweet_loop():
    await bot.wait_until_ready()
    delay = random.randint(0, 10)
    print(f"⏱️ Initial jitter delay: {delay}s")
    await asyncio.sleep(delay)

@bot.command()
async def tweet(ctx, url: str):
    """
    Manually post any tweet with working video embed
    Usage: !tweet https://twitter.com/user/status/123456
    """
    try:
        # Extract tweet ID and username from URL first
        match = re.search(r"(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)", url)
        
        if not match:
            return await ctx.send("❌ Invalid tweet URL. Use: `!tweet https://twitter.com/user/status/123`", delete_after=5)
        
        username = match.group(1)
        tweet_id = match.group(2)
        
        # Build FxTwitter link
        fxtwitter_url = f"https://fxtwitter.com/{username}/status/{tweet_id}"
        
        # Try to delete the user's command message to avoid duplicate embeds
        try:
            await ctx.message.delete()
        except discord.errors.Forbidden:
            print("⚠️ Bot lacks 'Manage Messages' permission")
        except Exception as e:
            print(f"⚠️ Could not delete message: {e}")
        
        # Send the FxTwitter link - Discord handles the rest!
        await ctx.send(fxtwitter_url)
        
        print(f"✅ Manual tweet posted: {tweet_id}")
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}", delete_after=5)
        print(f"❌ Command error: {e}")

@bot.command()
async def status(ctx):
    """Check bot status"""
    await ctx.send(
        f"✅ **Bot Status**\n"
        f"📺 Channel: <#{DISCORD_CHANNEL_ID}>\n"
        f"📝 Tracked tweets: {len(posted_tweets)}\n"
        f"🔄 Loop running: {tweet_loop.is_running()}"
    )

@bot.command()
async def clear(ctx):
    """Clear posted tweets history (admin only)"""
    global posted_tweets
    posted_tweets = []
    save_posted(posted_tweets)
    await ctx.send("✅ Cleared posted tweets history!")

# Run the bot
bot.run(DISCORD_TOKEN)
