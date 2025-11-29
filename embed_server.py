from flask import Flask, render_template_string, request
from urllib.parse import quote
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">

    <!-- TITLE + DESCRIPTION -->
    <meta property="og:title" content="{{ title }}">
    <meta property="og:description" content="{{ text[:200] }}">

    <!-- IMAGE PREVIEW -->
    {% if image_url %}
    <meta property="og:image" content="{{ image_url }}">
    {% endif %}

    <!-- VIDEO PREVIEW -->
    {% if video_url %}
    <meta property="og:video" content="{{ video_url }}">
    <meta property="og:type" content="video.other">
    <meta property="twitter:player" content="{{ video_url }}">
    {% endif %}

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
        .name {
            font-weight: 700;
            font-size: 16px;
        }
        .handle {
            color: #8899a6;
            font-size: 14px;
        }
        .text {
            font-size: 20px;
            line-height: 1.35;
            margin: 12px 0;
        }
        .media-container {
            margin-top: 16px;
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
            margin-top: 14px;
            padding-top: 14px;
            border-top: 1px solid #38444d;
            color: #8899a6;
            font-size: 14px;
        }
        .metric {
            display: flex;
            gap: 6px;
            align-items: center;
        }
    </style>
</head>

<body>
    <div class="container">
        <!-- HEADER -->
        <div class="name">{{ name }}</div>
        <div class="handle">@{{ handle }}</div>

        <!-- TEXT -->
        <div class="text">{{ text }}</div>

        <!-- VIDEO -->
        {% if video_url %}
        <div class="media-container">
            <video controls playsinline preload="none">
                <source src="{{ video_url }}" type="video/mp4">
                Video unsupported.
            </video>
        </div>
        {% elif image_url %}
        <!-- IMAGE -->
        <div class="media-container">
            <img src="{{ image_url }}">
        </div>
        {% endif %}

        <!-- METRICS -->
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


@app.route("/")
def tweet_embed():
    """
    Generate a FixTweet-style embed from URL query parameters.
    Discord unfurls this URL to show video/image inline.
    """

    title = request.args.get("title", "Tweet")
    name = request.args.get("name", "User")
    handle = request.args.get("handle", "user")
    text = request.args.get("text", "")

    video_url = request.args.get("video", None)
    image_url = request.args.get("image", None)

    likes = request.args.get("likes", 0)
    retweets = request.args.get("retweets", 0)
    replies = request.args.get("replies", 0)
    views = request.args.get("views", 0)

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
        views=views
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
