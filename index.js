import express from 'express';
import cors from 'cors';
import { fetchTweets } from './scraper.js';

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

app.get('/tweets/:username', async (req, res) => {
  const { username } = req.params;
  
  try {
    const tweets = await fetchTweets(username);
    res.json({ success: true, username, tweets });
  } catch (error) {
    console.error(`Error fetching tweets for @${username}:`, error.message);
    res.status(500).json({ 
      success: false, 
      error: error.message || 'Failed to fetch tweets',
      username 
    });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Twitter/X fetcher API is running' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Twitter/X Fetcher API running on http://0.0.0.0:${PORT}`);
  console.log(`📌 Try: http://localhost:${PORT}/tweets/NFL`);
});
