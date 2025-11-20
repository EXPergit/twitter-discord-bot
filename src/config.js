import dotenv from 'dotenv';

dotenv.config();

export const config = {
  discord: {
    token: process.env.DISCORD_BOT_TOKEN,
    channelId: process.env.DISCORD_CHANNEL_ID,
  },
  twitter: {
    bearerToken: process.env.TWITTER_BEARER_TOKEN,
    apiKey: process.env.TWITTER_API_KEY,
    apiSecret: process.env.TWITTER_API_SECRET,
    accessToken: process.env.TWITTER_ACCESS_TOKEN,
    accessSecret: process.env.TWITTER_ACCESS_SECRET,
    username: process.env.TWITTER_USERNAME || 'elonmusk',
  },
  pollIntervalMs: parseInt(process.env.POLL_INTERVAL_MS || '60000', 10),
};

export function validateConfig() {
  const errors = [];

  if (!config.discord.token) {
    errors.push('DISCORD_BOT_TOKEN is required');
  }
  if (!config.discord.channelId) {
    errors.push('DISCORD_CHANNEL_ID is required');
  }
  if (!config.twitter.bearerToken) {
    errors.push('TWITTER_BEARER_TOKEN is required');
  }

  if (errors.length > 0) {
    console.error('Configuration errors:');
    errors.forEach(error => console.error(`  - ${error}`));
    console.error('\nPlease check your .env file and ensure all required variables are set.');
    console.error('See .env.example for reference.');
    return false;
  }

  return true;
}
