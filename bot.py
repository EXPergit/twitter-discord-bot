import discord
from discord.ext import tasks
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import re
import time

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME", "nikhilraj__")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

LAST_TWEET_FILE = "last_tweet.json"

# Public Nitter instances (lightweight Twitter mirrors)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.1d4.us",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
]


class TwitterDiscordBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        
        self.channel = None
        self.last_tweet_id = self.load_last_tweet_id()
        self.session = requests.Session()
        self.current_nitter_index = 0

    def load_last_tweet_id(self):
        if os.path.exists(LAST_TWEET_FILE):
            try:
                with open(LAST_TWEET_FILE, "r") as f:
                    return json.load(f).get("last_tweet_id")
            except Exception as e:
                print(f"⚠️ Error loading last tweet: {e}")
        return None

    def save_last_tweet_id(self, tweet_id):
        try:
            with open(LAST_TWEET_FILE, "w") as f:
                json.dump({"last_tweet_id": tweet_id}, f)
            self.last_tweet_id = tweet_id
        except Exception as e:
            print(f"⚠️ Error saving last tweet: {e}")

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

        if not DISCORD_CHANNEL_ID:
            print("❌ DISCORD_CHANNEL_ID not set")
            await self.close()
            return

        self.channel = self.get_channel(int(DISCORD_CHANNEL_ID))
        if not self.channel:
            print(f"❌ Channel {DISCORD_CHANNEL_ID} not found")
            await self.close()
            return

        print(f"📡 Monitoring Twitter @{TWITTER_USERNAME}")
        print(f"🔑 Using Nitter (FREE - no API keys needed)")
        print(f"⏱️ Poll interval: {POLL_INTERVAL_SECONDS}s")

        self.check_tweets.start()

    @tasks.loop(seconds=POLL_INTERVAL_SECONDS)
    async def check_tweets(self):
        print("🔍 Checking for new tweets…")

        tweets = await self.get_new_tweets()
        if not tweets:
            print("📭 No new tweets")
            return

        print(f"📬 Found {len(tweets)} new tweet(s)")
        for tweet in tweets:
            await self.post_tweet_to_discord(tweet)
            await asyncio.sleep(1)

    @check_tweets.before_loop
    async def before_check_tweets(self):
        await self.wait_until_ready()

    async def get_new_tweets(self):
        """Fetch tweets from Nitter (lightweight Twitter mirror)"""
        for instance_idx, nitter_base in enumerate(NITTER_INSTANCES):
            try:
                url = f"{nitter_base}/{TWITTER_USERNAME}"
                print(f"🌐 Trying Nitter instance: {nitter_base}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
                
                response = self.session.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                print(f"✅ Got response from {nitter_base}")
                tweets = self.parse_nitter_html(response.text)
                
                if tweets:
                    print(f"✅ Found {len(tweets)} tweets!")
                    self.save_last_tweet_id(tweets[0]["id"])
                    self.current_nitter_index = instance_idx
                    return tweets
                    
            except Exception as e:
                print(f"⚠️ Failed with {nitter_base}: {str(e)[:50]}")
                time.sleep(1)
                continue
        
        print("❌ All Nitter instances failed")
        return []

    def parse_nitter_html(self, html):
        """Parse tweets from Nitter HTML"""
        tweets = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find tweet items in Nitter format
            # Nitter uses 'class="tweet' for tweet containers
            tweet_divs = soup.find_all('div', class_='timeline-item')
            print(f"🔍 Found {len(tweet_divs)} tweet items")
            
            if not tweet_divs:
                # Try alternative Nitter structure
                tweet_divs = soup.find_all('div', class_='tweet')
            
            for tweet_div in tweet_divs[:15]:  # Check up to 15 tweets
                try:
                    # Get tweet link
                    link = tweet_div.find('a', href=re.compile(r'/\w+/status/\d+'))
                    if not link:
                        continue
                    
                    href = link.get('href', '')
                    match = re.search(r'/status/(\d+)', href)
                    if not match:
                        continue
                    
                    tweet_id = match.group(1)
                    
                    # Skip if already processed
                    if self.last_tweet_id and int(tweet_id) <= int(self.last_tweet_id):
                        continue
                    
                    # Get tweet text
                    text_elem = tweet_div.find('div', class_='tweet-text')
                    if not text_elem:
                        text_elem = tweet_div.find('p', class_='tweet-text')
                    
                    text = ""
                    if text_elem:
                        text = text_elem.get_text(strip=True)[:280]
                    
                    # Clean whitespace
                    text = ' '.join(text.split())
                    
                    if not text or len(text) < 3:
                        continue
                    
                    tweets.append({
                        'id': tweet_id,
                        'content': text,
                        'url': f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet_id}",
                    })
                    
                except Exception as e:
                    continue
            
            print(f"💾 Extracted {len(tweets)} valid tweets")
            return list(reversed(tweets))[:5]  # Return up to 5 latest
            
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return []

    async def post_tweet_to_discord(self, tweet):
        try:
            embed = discord.Embed(
                description=tweet.get("content", "")[:2000],
                color=0x1DA1F2,
                timestamp=datetime.now(),
                url=tweet.get("url", "")
            )

            embed.set_author(
                name=f"@{TWITTER_USERNAME}",
                url=f"https://twitter.com/{TWITTER_USERNAME}",
            )

            embed.set_footer(text="Twitter • via Nitter")

            await self.channel.send(embed=embed)
            print(f"✅ Posted tweet {tweet['id']}")

        except Exception as e:
            print(f"❌ Error posting: {e}")


def validate_config():
    errors = []
    
    if not DISCORD_BOT_TOKEN:
        errors.append("DISCORD_BOT_TOKEN is required")
    if not DISCORD_CHANNEL_ID:
        errors.append("DISCORD_CHANNEL_ID is required")
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Starting Twitter to Discord bot (Nitter)...")
    
    if not validate_config():
        exit(1)
    
    bot = TwitterDiscordBot()
    bot.run(DISCORD_BOT_TOKEN)
