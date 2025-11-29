import discord
from discord.ext import commands, tasks
import os
import requests
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID_2', 0))
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Track posted tweets to avoid duplicates
POSTED_TWEETS_FILE = 'posted_tweets2.json'

def load_posted_tweets():
    if Path(POSTED_TWEETS_FILE).exists():
        try:
            return json.load(open(POSTED_TWEETS_FILE))
        except:
            return {}
    return {}

def save_posted_tweets(data):
    json.dump(data, open(POSTED_TWEETS_FILE, 'w'), indent=2)

def get_tweets(username):
    """Fetch tweets from Twitter API v2 with media"""
    if not TWITTER_BEARER_TOKEN:
        return []
    
    try:
        headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}
        max_retries = 3
        
        # Get user ID with retries for rate limiting
        for attempt in range(max_retries):
            user_url = f'https://api.twitter.com/2/users/by/username/{username}'
            user_response = requests.get(user_url, headers=headers, timeout=10)
            
            if user_response.status_code == 429:
                import time
                wait = 2 ** attempt
                print(f"⏳ Rate limited (user lookup). Waiting {wait}s…")
                time.sleep(wait)
                continue
            
            if user_response.status_code != 200:
                print(f"❌ User lookup failed: {user_response.status_code}")
                return []
            break
        
        user_id = user_response.json()['data']['id']
        
        # Get tweets with media - with retries for rate limiting
        tweets_url = f'https://api.twitter.com/2/users/{user_id}/tweets'
        params = {
            'max_results': 5,
            'tweet.fields': 'created_at,public_metrics',
            'expansions': 'attachments.media_keys,author_id',
            'media.fields': 'media_key,type,url,preview_image_url,variants,public_metrics'
        }
        
        for attempt in range(max_retries):
            tweets_response = requests.get(tweets_url, headers=headers, params=params, timeout=10)
            
            if tweets_response.status_code == 429:
                import time
                wait = 2 ** attempt
                print(f"⏳ Rate limited (tweets fetch). Waiting {wait}s…")
                time.sleep(wait)
                continue
            
            if tweets_response.status_code != 200:
                print(f"❌ Tweets lookup failed: {tweets_response.status_code}")
                return []
            break
        
        response_data = tweets_response.json()
        tweets = []
        media_dict = {}
        
        # Build media lookup
        if 'includes' in response_data and 'media' in response_data['includes']:
            for media in response_data['includes']['media']:
                media_dict[media['media_key']] = media
        
        if 'data' in response_data:
            for tweet in response_data['data']:
                media_list = []
                
                # Extract media from tweet
                if 'attachments' in tweet and 'media_keys' in tweet['attachments']:
                    for media_key in tweet['attachments']['media_keys']:
                        if media_key in media_dict:
                            media = media_dict[media_key]
                            video_url = None
                            
                            # Extract video URL from variants if available
                            if media.get('type') in ['video', 'animated_gif'] and 'variants' in media:
                                for variant in media['variants']:
                                    if variant.get('content_type') == 'video/mp4':
                                        video_url = variant.get('url')
                                        break
                            
                            media_list.append({
                                'type': media.get('type'),
                                'url': media.get('url'),
                                'preview_image_url': media.get('preview_image_url'),
                                'video_url': video_url
                            })
                
                tweets.append({
                    'id': tweet['id'],
                    'text': tweet['text'],
                    'url': f'https://x.com/{username}/status/{tweet["id"]}',
                    'created_at': tweet.get('created_at', ''),
                    'metrics': tweet.get('public_metrics', {}),
                    'media': media_list
                })
        
        return tweets
    except Exception as e:
        print(f"❌ Error fetching tweets: {e}")
        return []

async def fetch_startup_tweets():
    """Fetch tweets on startup with exponential backoff (max 12 retries)."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("❌ No channel found.")
        return

    print("📌 Fetching top 2 tweets…")

    max_retries = 12
    for attempt in range(max_retries):
        tweets = get_tweets('arkdesignss')

        if tweets:
            print("✅ Startup tweets fetched.")
            posted = load_posted_tweets()
            for t in tweets[:2]:
                try:
                    embed = discord.Embed(title=t['text'][:200], description=f"[View Tweet]({t['url']})", color=0x1F51BA)
                    embed.set_author(name='@arkdesignss', url=t['url'])
                    
                    m = t['metrics']
                    metrics_text = f"💬 {m.get('reply_count', 0)}   🔄 {m.get('retweet_count', 0)}   ❤️ {m.get('like_count', 0)}   👁️ {m.get('impression_count', 0)}"
                    embed.add_field(name=metrics_text, value="", inline=False)
                    
                    if t['media']:
                        for media in t['media']:
                            if media['type'] == 'photo':
                                embed.set_image(url=media.get('url'))
                            elif media['type'] in ['video', 'animated_gif']:
                                embed.set_image(url=media.get('preview_image_url'))
                    
                    embed.set_footer(text='X.com')
                    await channel.send(embed=embed, content=t['url'])
                    posted[t['id']] = True
                except Exception as e:
                    print(f"❌ Error posting: {e}")
            
            save_posted_tweets(posted)
            return

        if attempt < max_retries - 1:
            wait = min(5 * (2 ** attempt), 300)  # Exponential backoff, max 5min
            print(f"⏳ Rate limited. Retry {attempt + 1}/{max_retries} in {wait}s…")
            await asyncio.sleep(wait)
    
    print("❌ Failed to fetch tweets after max retries. Giving up for now.")

@bot.event
async def on_ready():
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📢 Target channel: {DISCORD_CHANNEL_ID}')
    
    await fetch_startup_tweets()
    
    if not tweet_checker.is_running():
        tweet_checker.start()
        print('🔄 Tweet checker started')

@tasks.loop(minutes=5)
async def tweet_checker():
    """Check for new tweets every 5 minutes"""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return
    
    posted = load_posted_tweets()
    tweets = get_tweets('arkdesignss')
    
    if not tweets:
        print("ℹ️  No tweets found")
        return
    
    for tweet in reversed(tweets):
        if tweet['id'] in posted:
            continue
        
        try:
            # Create embed with link
            embed = discord.Embed(
                title="Tweet from @arkdesignss",
                description=tweet['text'][:2000],
                url=tweet['url'],
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Link", value=tweet['url'], inline=False)
            if tweet['metrics']:
                embed.add_field(name="❤️ Likes", value=str(tweet['metrics'].get('like_count', 0)), inline=True)
                embed.add_field(name="🔄 Retweets", value=str(tweet['metrics'].get('retweet_count', 0)), inline=True)
            embed.set_footer(text="X.com")
            
            # Add media to embed
            video_url = None
            if tweet['media']:
                for media in tweet['media']:
                    if media['type'] == 'photo' and media.get('url'):
                        embed.set_image(url=media['url'])
                        break
                    elif media['type'] in ['video', 'animated_gif']:
                        if media.get('video_url'):
                            video_url = media['video_url']
                        break
            
            await channel.send(embed=embed)
            
            # Send video as separate message so Discord renders playable player
            if video_url:
                await channel.send(video_url)
            
            print(f"✅ Posted tweet {tweet['id']}")
            
            posted[tweet['id']] = True
            save_posted_tweets(posted)
        except Exception as e:
            print(f"❌ Error posting: {e}")

@tweet_checker.before_loop
async def before_tweet_checker():
    await bot.wait_until_ready()

@bot.command()
async def check(ctx):
    """Manually check for new tweets"""
    await ctx.send("🔍 Checking for new tweets...")
    tweets = get_tweets('arkdesignss')
    if tweets:
        await ctx.send(f"✅ Found {len(tweets)} tweets")
    else:
        await ctx.send("❌ No tweets found")

if __name__ == '__main__':
    if not DISCORD_TOKEN or not DISCORD_CHANNEL_ID or not TWITTER_BEARER_TOKEN:
        print('❌ Missing DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, or TWITTER_BEARER_TOKEN')
        exit(1)
    print('🚀 Starting Twitter to Discord Bot...')
    bot.run(DISCORD_TOKEN)
