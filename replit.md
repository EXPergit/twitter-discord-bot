# Twitter to Discord Bot

## Overview
A Node.js Discord bot that monitors a specific Twitter account and automatically posts new tweets with embedded videos to a designated Discord channel. Built with discord.js v14 and twitter-api-v2.

## Purpose
This bot enables real-time monitoring of Twitter accounts and automatic cross-posting to Discord, with special handling for video content to ensure videos are embedded and playable directly within Discord messages.

## Project Architecture

### Technology Stack
- **Runtime**: Node.js 20
- **Discord Integration**: discord.js v14
- **Twitter Integration**: twitter-api-v2
- **Configuration**: dotenv for environment variables

### Project Structure
```
├── src/
│   ├── index.js           # Main entry point, orchestrates bot lifecycle
│   ├── config.js          # Configuration loading and validation
│   ├── discordBot.js      # Discord client and message posting
│   └── twitterService.js  # Twitter API integration and tweet fetching
├── .env                   # Environment configuration (user-provided)
├── .env.example          # Configuration template
├── package.json          # Dependencies and scripts
└── tweets.json           # Persistent storage for last processed tweet ID
```

### Key Features
1. **Real-time Tweet Monitoring**: Polls Twitter API v2 at configurable intervals
2. **Video Detection**: Identifies videos in tweets (native Twitter videos and external links)
3. **Discord Embedding**: Posts tweets with rich embeds and embedded video content
4. **State Persistence**: Tracks last processed tweet to prevent duplicates
5. **Rate Limit Handling**: Implements backoff strategy for Twitter API limits
6. **Error Handling**: Comprehensive error logging and graceful degradation

### Configuration
The bot requires several environment variables:
- Discord: Bot token and target channel ID
- Twitter: Bearer token and username to monitor
- Settings: Poll interval (default 60 seconds)

## Recent Changes
- **2025-11-20**: Initial project setup
  - Installed Node.js 20 and dependencies (discord.js, twitter-api-v2, dotenv)
  - Created modular architecture with separate files for Discord, Twitter, and config
  - Implemented polling-based tweet monitoring with state persistence
  - Added video detection for both native Twitter videos and external video links
  - Created comprehensive documentation and setup guide

## Current State
The bot is fully implemented and ready to run. Users need to:
1. Configure `.env` file with their credentials
2. Run `npm start` to start the bot

## Dependencies
- discord.js: Discord bot API client
- twitter-api-v2: Twitter API v2 client with full featured support
- dotenv: Environment variable management
