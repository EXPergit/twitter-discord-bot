import discord
from discord.ext import commands, tasks
import os
import json
import aiohttp
from datetime import datetime
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
TWITTER_USERNAME = os.getenv('TWITTER_USERNAME', 'NFL')
FETCHER_URL = os.getenv('FETCHER_URL', 'http://localhost:5000')

# State file for tracking posted tweets
STATE_FILE = 'posted_tweets.json'

def load_posted_tweets():
    """Load the list of already-posted tweet IDs"""
    if Path(STATE_FILE).exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_posted_tweets(tweet_ids):
    """Save the list of posted tweet IDs"""
    with open(STATE_FILE, 'w') as f:
        json.dump(tweet_ids, f)

# Initialize bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

posted_tweets = load_posted_tweets()

@bot.event
async def on_ready():
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📌 Monitoring @{TWITTER_USERNAME}')
    print(f'📢 Posting to Discord channel: {DISCORD_CHANNEL_ID}')
    fetch_tweets_loop.start()

@tasks.loop(minutes=1)
async def fetch_tweets_loop():
    """Periodically fetch tweets and post to Discord"""
    global posted_tweets
    
    try:
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        if not channel:
            print(f'❌ Channel {DISCORD_CHANNEL_ID} not found')
            return
        
        # Fetch tweets from the Node.js API
        async with aiohttp.ClientSession() as session:
            url = f'{FETCHER_URL}/tweets/{TWITTER_USERNAME}'
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f'⚠️ Failed to fetch tweets: HTTP {resp.status}')
                    return
                
                data = await resp.json()
                
                if not data.get('success'):
                    print(f'⚠️ API error: {data.get("error")}')
                    return
                
                tweets = data.get('tweets', [])
                
                if not tweets:
                    print('ℹ️ No tweets found')
                    return
                
                # Post new tweets
                new_count = 0
                for tweet in tweets:
                    tweet_id = tweet.get('id')
                    
                    # Skip if already posted
                    if tweet_id in posted_tweets:
                        continue
                    
                    try:
                        # Create embed for the tweet
                        embed = discord.Embed(
                            title=f"New Tweet from @{TWITTER_USERNAME}",
                            description=tweet.get('text', 'No text'),
                            url=tweet.get('url'),
                            color=discord.Color.blue(),
                            timestamp=datetime.fromisoformat(tweet.get('timestamp', datetime.now().isoformat()))
                        )
                        embed.set_footer(text="Posted from X.com")
                        
                        # Send to Discord
                        await channel.send(embed=embed)
                        
                        # Mark as posted
                        posted_tweets.append(tweet_id)
                        new_count += 1
                        
                        print(f'✅ Posted tweet {tweet_id}')
                    except Exception as e:
                        print(f'❌ Error posting tweet {tweet_id}: {e}')
                
                # Save state
                if new_count > 0:
                    save_posted_tweets(posted_tweets)
                    print(f'💾 Saved {new_count} new tweet(s)')
    
    except Exception as e:
        print(f'❌ Error in fetch_tweets_loop: {e}')

@fetch_tweets_loop.before_loop
async def before_fetch_tweets_loop():
    """Wait for bot to be ready before starting the loop"""
    await bot.wait_until_ready()

# Run the bot
if __name__ == '__main__':
    if not DISCORD_BOT_TOKEN:
        print('❌ DISCORD_BOT_TOKEN not set in .env')
        exit(1)
    if not DISCORD_CHANNEL_ID or DISCORD_CHANNEL_ID == 0:
        print('❌ DISCORD_CHANNEL_ID not set in .env')
        exit(1)
    
    print('🚀 Starting Discord bot...')
    bot.run(DISCORD_BOT_TOKEN)
