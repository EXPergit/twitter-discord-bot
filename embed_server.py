from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta property="og:title" content="{{ title }}">
    <meta property="og:description" content="{{ text }}">
    <meta property="og:image" content="{{ image_url }}">
    <meta property="og:video" content="{{ video_url }}">
    <meta property="og:video:type" content="video/mp4">
    <meta property="og:video:width" content="1280">
    <meta property="og:video:height" content="720">
    <meta name="twitter:card" content="player">
    <meta name="twitter:player" content="{{ video_url }}">
    <meta name="twitter:player:width" content="1280">
    <meta name="twitter:player:height" content="720">
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
        .header-info {
            flex: 1;
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
        .video-container {
            margin: 16px 0;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
        }
        video {
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
        .footer {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #38444d;
            color: #657786;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-info">
                <div class="name">{{ name }}</div>
                <div class="handle">@{{ handle }}</div>
            </div>
        </div>
        <div class="text">{{ text }}</div>
        {% if video_url %}
        <div class="video-container">
            <video controls width="600" height="auto">
                <source src="{{ video_url }}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        {% elif image_url %}
        <img src="{{ image_url }}" style="width: 100%; border-radius: 12px; margin: 16px 0;">
        {% endif %}
        <div class="metrics">
            <div class="metric">💬 <strong>{{ replies }}</strong></div>
            <div class="metric">🔄 <strong>{{ retweets }}</strong></div>
            <div class="metric">❤️ <strong>{{ likes }}</strong></div>
            <div class="metric">👁️ <strong>{{ views }}</strong></div>
        </div>
        <div class="footer">Posted on X.com</div>
    </div>
</body>
</html>
"""

@app.route('/tweet/<tweet_id>/<handle>/<int:likes>/<int:retweets>/<int:replies>/<int:views>/<path:text_and_media>')
def tweet_embed(tweet_id, handle, likes, retweets, replies, views, text_and_media):
    """Generate a fixtweet-style embed page"""
    parts = text_and_media.rsplit('/', 2)
    text = parts[0] if len(parts) > 1 else text_and_media
    video_url = parts[1] if len(parts) > 2 and parts[1] else None
    image_url = parts[2] if len(parts) > 2 and parts[2] else None
    
    return render_template_string(
        HTML_TEMPLATE,
        title=f"Tweet from @{handle}",
        name=handle.upper(),
        handle=handle,
        text=text[:500],
        video_url=video_url if video_url != "none" else None,
        image_url=image_url if image_url != "none" else None,
        likes=likes,
        retweets=retweets,
        replies=replies,
        views=views
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
