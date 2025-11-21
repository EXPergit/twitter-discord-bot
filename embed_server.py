from flask import Flask, render_template_string, request
from urllib.parse import quote
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta property="og:title" content="{{ title }}">
    <meta property="og:description" content="{{ text[:100] }}">
    {% if video_url %}
    <meta property="og:video" content="{{ video_url }}">
    <meta property="og:video:type" content="video/mp4">
    <meta property="og:video:width" content="1280">
    <meta property="og:video:height" content="720">
    {% elif image_url %}
    <meta property="og:image" content="{{ image_url }}">
    {% endif %}
    <meta name="twitter:card" content="player">
    <meta property="twitter:player" content="{{ request.url_root }}static/player.html?v={{ video_url }}">
    <title>{{ title }}</title>
    <style>
        body {
            background: #0f1419;
            color: #e7e9ea;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: #192734;
            border-radius: 16px;
            padding: 16px;
            border: 1px solid #38444d;
        }
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        .name {
            font-weight: 700;
            font-size: 15px;
        }
        .handle {
            color: #657786;
            font-size: 15px;
        }
        .text {
            font-size: 20px;
            line-height: 1.3;
            margin: 12px 0;
            word-wrap: break-word;
        }
        .media-container {
            margin: 16px -16px 0 -16px;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
        }
        video, img {
            width: 100%;
            height: auto;
            display: block;
        }
        .metrics {
            display: flex;
            gap: 16px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #38444d;
            color: #657786;
            font-size: 13px;
        }
        .metric {
            display: flex;
            gap: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <div class="name">{{ name }}</div>
                <div class="handle">@{{ handle }}</div>
            </div>
        </div>
        <div class="text">{{ text }}</div>
        {% if video_url %}
        <div class="media-container">
            <video controls width="100%" style="background: #000;">
                <source src="{{ video_url }}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        {% elif image_url %}
        <div class="media-container">
            <img src="{{ image_url }}" />
        </div>
        {% endif %}
        <div class="metrics">
            <div class="metric">💬 <strong>{{ replies }}</strong></div>
            <div class="metric">🔄 <strong>{{ retweets }}</strong></div>
            <div class="metric">❤️ <strong>{{ likes }}</strong></div>
            <div class="metric">👁️ <strong>{{ views }}</strong></div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def tweet_embed():
    """Generate a fixtweet-style embed page with query parameters"""
    title = request.args.get('title', 'Tweet')
    name = request.args.get('name', 'User')
    handle = request.args.get('handle', 'user')
    text = request.args.get('text', '')
    video_url = request.args.get('video', None)
    image_url = request.args.get('image', None)
    likes = request.args.get('likes', 0)
    retweets = request.args.get('retweets', 0)
    replies = request.args.get('replies', 0)
    views = request.args.get('views', 0)
    
    return render_template_string(
        HTML_TEMPLATE,
        title=title,
        name=name,
        handle=handle,
        text=text[:500],
        video_url=video_url,
        image_url=image_url,
        likes=likes,
        retweets=retweets,
        replies=replies,
        views=views,
        request=request
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
