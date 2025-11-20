# Twitter to Discord Bot with Puppeteer Scraper

## Overview
A dual-component system that monitors Twitter/X accounts and automatically posts tweets to Discord. Uses a Node.js Express server with Puppeteer for web scraping (free alternative to Twitter API) and a Python Discord bot for posting.

## Purpose
Enable real-time Twitter/X monitoring and automatic cross-posting to Discord without requiring expensive API credentials. The Puppeteer scraper handles tweet extraction via browser automation, while the Discord bot manages the communication with Discord servers.

## Project Architecture

### Technology Stack
- **Frontend Scraper**: Node.js + Express + Puppeteer (browser automation, free scraping)
- **Discord Integration**: Python + discord.py (bot for posting to Discord)
- **Configuration**: python-dotenv for environment variables
- **Authentication**: Cookie-based X.com authentication (optional)

### Project Structure
```
├── index.js              # Express server with /tweets/:username endpoint
├── scraper.js            # Puppeteer logic for tweet extraction
├── discord_bot.py        # Discord bot that polls API and posts tweets
├── cookies.json          # Optional X.com cookies for authentication
├── .env                  # Environment configuration (user-provided)
├── .env.example          # Configuration template
├── posted_tweets.json    # Persistent storage of posted tweet IDs
└── README.md             # Setup instructions
```

### Key Features
1. **Free Tweet Monitoring**: Puppeteer browser automation (no API costs)
2. **Automatic Scrolling**: Loads 10-20+ tweets per request
3. **Discord Integration**: Posts tweets with rich embeds
4. **Duplicate Prevention**: Tracks posted tweets to avoid repeats
5. **State Persistence**: Remembers which tweets have been posted
6. **Cookie Authentication**: Optional X.com login for authenticated scraping
7. **Simple Setup**: No Twitter API credentials needed

### Configuration
The system requires Discord credentials:
- **Discord**: Bot token and target channel ID
- **Twitter**: Username to monitor (no API keys!)
- **API**: Fetcher URL (default: http://localhost:5000)

## Recent Changes
- **2025-11-20**: Integrated Puppeteer scraper with Discord bot
  - Created Node.js Express server with `/tweets/:username` endpoint
  - Implemented Puppeteer browser automation for tweet scraping
  - Created Python Discord bot that polls the API and posts tweets
  - Added state persistence to track posted tweets
  - Installed all system dependencies for headless Chrome

## Current State
The system is fully implemented with two components:
1. **Twitter Fetcher API** (Node.js) - Running on port 5000
2. **Discord Bot** (Python) - Ready to start

To run:
```bash
# Terminal 1: Start the Twitter fetcher API
node index.js

# Terminal 2: Start the Discord bot (in a separate workflow)
python discord_bot.py
```

## Environment Variables Required
- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `DISCORD_CHANNEL_ID` - Target Discord channel ID
- `TWITTER_USERNAME` - Username to monitor (default: NFL)
- `FETCHER_URL` - URL of the fetcher API (default: http://localhost:5000)

## Dependencies
- **Node.js**: express, puppeteer, cors
- **Python**: discord.py, aiohttp, python-dotenv

## User Preferences
- Prefers free/low-cost solutions (no paid APIs)
- Building for personal use
- Wants simplified, working solution

## Technical Notes
- Puppeteer uses headless Chromium with required system libraries (glib, gtk3, pango, etc.)
- Discord bot polls every 1 minute for new tweets
- Tweet state is persisted in `posted_tweets.json`
- Optional X.com cookies can be added to `cookies.json` for authenticated scraping
