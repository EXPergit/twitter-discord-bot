import { TwitterApi } from 'twitter-api-v2';
import { config } from './config.js';
import fs from 'fs';

const LAST_TWEET_FILE = 'tweets.json';

export class TwitterService {
  constructor() {
    this.client = new TwitterApi(config.twitter.bearerToken);
    this.readOnlyClient = this.client.readOnly;
    this.userId = null;
    this.lastTweetId = null;
    this.loadLastTweetId();
  }

  loadLastTweetId() {
    try {
      if (fs.existsSync(LAST_TWEET_FILE)) {
        const data = JSON.parse(fs.readFileSync(LAST_TWEET_FILE, 'utf8'));
        this.lastTweetId = data.lastTweetId;
        console.log(`📝 Loaded last tweet ID: ${this.lastTweetId}`);
      }
    } catch (error) {
      console.error('Error loading last tweet ID:', error.message);
    }
  }

  saveLastTweetId(tweetId) {
    try {
      fs.writeFileSync(LAST_TWEET_FILE, JSON.stringify({ lastTweetId: tweetId }));
      this.lastTweetId = tweetId;
    } catch (error) {
      console.error('Error saving last tweet ID:', error.message);
    }
  }

  async getUserId() {
    if (this.userId) {
      return this.userId;
    }

    try {
      const user = await this.readOnlyClient.v2.userByUsername(config.twitter.username);
      this.userId = user.data.id;
      console.log(`✅ Found Twitter user: @${config.twitter.username} (ID: ${this.userId})`);
      return this.userId;
    } catch (error) {
      console.error('Error fetching user ID:', error);
      throw error;
    }
  }

  async getLatestTweets() {
    try {
      const userId = await this.getUserId();

      const params = {
        max_results: 10,
        'tweet.fields': ['created_at', 'attachments', 'entities'],
        'user.fields': ['name', 'username', 'profile_image_url'],
        'media.fields': ['type', 'url', 'preview_image_url', 'variants'],
        expansions: ['author_id', 'attachments.media_keys'],
      };

      if (this.lastTweetId) {
        params.since_id = this.lastTweetId;
      }

      const timeline = await this.readOnlyClient.v2.userTimeline(userId, params);

      if (!timeline.tweets || timeline.tweets.length === 0) {
        return [];
      }

      const tweets = timeline.tweets;
      const includes = timeline.includes || {};
      const users = includes.users || [];
      const media = includes.media || [];

      const processedTweets = tweets.map(tweet => {
        const author = users.find(u => u.id === tweet.author_id) || {
          name: config.twitter.username,
          username: config.twitter.username,
          profile_image_url: '',
        };

        let video = null;
        if (tweet.attachments && tweet.attachments.media_keys) {
          const tweetMedia = media.filter(m => 
            tweet.attachments.media_keys.includes(m.media_key)
          );

          const videoMedia = tweetMedia.find(m => m.type === 'video' || m.type === 'animated_gif');
          if (videoMedia && videoMedia.variants) {
            const mp4Variants = videoMedia.variants.filter(v => v.content_type === 'video/mp4');
            if (mp4Variants.length > 0) {
              const highestQuality = mp4Variants.sort((a, b) => (b.bit_rate || 0) - (a.bit_rate || 0))[0];
              video = {
                url: highestQuality.url,
                type: videoMedia.type,
              };
            }
          }
        }

        if (!video && tweet.entities && tweet.entities.urls) {
          const videoUrls = tweet.entities.urls.filter(url => 
            url.expanded_url && (
              url.expanded_url.includes('youtube.com') ||
              url.expanded_url.includes('youtu.be') ||
              url.expanded_url.includes('vimeo.com')
            )
          );
          if (videoUrls.length > 0) {
            video = {
              url: videoUrls[0].expanded_url,
              type: 'external',
            };
          }
        }

        return {
          id: tweet.id,
          text: tweet.text,
          created_at: tweet.created_at,
          author,
          video,
        };
      });

      if (processedTweets.length > 0) {
        this.saveLastTweetId(processedTweets[0].id);
      }

      return processedTweets.reverse();
    } catch (error) {
      if (error.code === 429) {
        console.error('⚠️  Rate limit exceeded. Waiting before next request...');
        throw new Error('RATE_LIMIT');
      }
      console.error('Error fetching tweets:', error);
      throw error;
    }
  }
}
