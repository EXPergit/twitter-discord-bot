import sys
import json
import requests
import os

def fetch_tweets_api(username):
    """Fetch tweets using Twitter API v2"""
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    
    if not bearer_token:
        return []
    
    try:
        # Step 1: Get user ID
        headers = {'Authorization': f'Bearer {bearer_token}'}
        user_url = f'https://api.twitter.com/2/users/by/username/{username}'
        user_response = requests.get(user_url, headers=headers, timeout=10)
        
        if user_response.status_code != 200:
            print(f"User lookup failed: {user_response.status_code}", file=sys.stderr)
            return []
        
        user_id = user_response.json()['data']['id']
        
        # Step 2: Get recent tweets
        tweets_url = f'https://api.twitter.com/2/users/{user_id}/tweets'
        params = {
            'max_results': 20,
            'tweet.fields': 'created_at',
            'expansions': 'author_id'
        }
        
        tweets_response = requests.get(tweets_url, headers=headers, params=params, timeout=10)
        
        if tweets_response.status_code != 200:
            print(f"Tweets lookup failed: {tweets_response.status_code}", file=sys.stderr)
            return []
        
        data = tweets_response.json()
        tweets = []
        
        if 'data' in data:
            for tweet in data['data']:
                tweets.append({
                    'id': tweet['id'],
                    'text': tweet['text'],
                    'url': f'https://x.com/{username}/status/{tweet["id"]}',
                    'timestamp': tweet.get('created_at', '')
                })
        
        return tweets
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return []

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps([]))
        sys.exit(0)
    
    username = sys.argv[1].lstrip('@')
    tweets = fetch_tweets_api(username)
    print(json.dumps(tweets))
