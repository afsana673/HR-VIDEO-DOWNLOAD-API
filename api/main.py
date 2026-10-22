"""HR VIDEO DOWNLOADER API — metadata and direct video links only.
Developer: SK HABIBULLA
"""

import os
import secrets
import shutil
from urllib.parse import urlsplit

import yt_dlp
from flask import Flask, jsonify, request
from yt_dlp.utils import DownloadError

app = Flask(__name__)

HOSTS = {
    "instagram": ("instagram.com", "instagr.am"),
    "facebook": ("facebook.com", "fb.com", "fb.watch"),
    "youtube": ("youtube.com", "youtu.be", "youtube-nocookie.com"),
    "pinterest": (
        "pinterest.com", "pinterest.in", "pinterest.co.uk",
        "pinterest.ca", "pinterest.com.au", "pinterest.fr",
        "pinterest.de", "pinterest.es", "pin.it",
    ),
}
QUALITIES = {"best", "360", "480", "720", "1080"}


@app.after_request
def cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
    response.headers["Cache-Control"] = "no-store"
    return response


def platform_from_url(raw_url):
    try:
        parts = urlsplit(raw_url.strip())
        host = (parts.hostname or "").lower().rstrip(".")
        if parts.scheme not in ("http", "https") or not host:
            return None
        if parts.username or parts.password or parts.port not in (None, 80, 443):
            return None
        for platform, domains in HOSTS.items():
            if any(host == domain or host.endswith("." + domain) for domain in domains):
                return platform
    except (ValueError, AttributeError):
        pass
    return None


def get_video(url, quality):
    platform = platform_from_url(url)
    if not platform:
        raise ValueError("শুধু Instagram, Facebook, YouTube বা Pinterest-এর বৈধ লিংক দিন।")

    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "playlistend": 1,
        "socket_timeout": 15,
        "retries": 1,
        "extractor_retries": 1,
    }
    if shutil.which("node"):
        options["js_runtimes"] = {"node": {}}

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise ValueError("ভিডিওর তথ্য পাওয়া যায়নি।")
    if info.get("_type") in ("playlist", "multi_video"):
        entries = [entry for entry in (info.get("entries") or []) if entry]
        if not entries:
            raise ValueError("এই লিংকে পাবলিক ভিডিও পাওয়া যায়নি।")
        info = entries[0]

    formats = info.get("formats") or [info]
    candidates = []
    for fmt in formats:
        media_url = fmt.get("url") or ""
        ext = (fmt.get("ext") or "").lower()
        protocol = (fmt.get("protocol") or "https").lower()
        if not media_url.startswith(("https://", "http://")):
            continue
        if protocol not in ("http", "https") or ext not in ("mp4", "webm"):
            continue
        if fmt.get("vcodec") == "none" or fmt.get("acodec") == "none":
            continue
        candidates.append(fmt)

    if not candidates:
        raise ValueError(
            "সরাসরি MP4/WebM (ভিডিও+অডিও) লিংক পাওয়া যায়নি। "
            "এই ভিডিওর জন্য আলাদা audio/video merge বা login লাগতে পারে।"
        )

    if quality == "best":
        chosen = max(candidates, key=lambda f: (
            f.get("height") or 0, f.get("ext") == "mp4", f.get("tbr") or 0
        ))
    else:
        limit = int(quality)
        below = [f for f in candidates if (f.get("height") or 0) <= limit]
        if below:
            chosen = max(below, key=lambda f: (
                f.get("height") or 0, f.get("ext") == "mp4", f.get("tbr") or 0
            ))
        else:
            chosen = min(candidates, key=lambda f: (
                f.get("height") or 99999, f.get("ext") != "mp4"
            ))

    available = [
        f"{height}p"
        for height in sorted({int(f["height"]) for f in candidates if f.get("height")})
    ]
    headers = chosen.get("http_headers") or info.get("http_headers") or {}
    safe_headers = {
        key: value for key, value in headers.items()
        if key.lower() in {"user-agent", "referer", "origin"}
        and isinstance(value, str)
    }

    return {
        "success": True,
        "developer": "SK HABIBULLA",
        "platform": platform,
        "title": info.get("title") or "Untitled video",
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader"),
        "quality": f"{chosen['height']}p" if chosen.get("height") else "unknown",
        "available_qualities": available,
        "extension": chosen.get("ext"),
        "download_url": chosen["url"],
        "request_headers": safe_headers,
        "note": "লিংকটি অস্থায়ী হতে পারে; কিছু CDN-এ বিশেষ headers/IP প্রয়োজন হয়।",
    }


@app.get("/")
def home():
    return jsonify({
        "success": True,
        "api": "HR VIDEO DOWNLOADER",
        "developer": "SK HABIBULLA",
        "endpoint": "/api/download",
        "usage": "/api/download?url=VIDEO_URL&quality=best",
        "qualities": ["best", "360", "480", "720", "1080"],
        "platforms": list(HOSTS),
    })


@app.route("/api/download", methods=["GET", "OPTIONS"])
def download():
    if request.method == "OPTIONS":
        return ("", 204)

    configured_key = os.getenv("DOWNLOAD_API_KEY", "")
    supplied_key = request.headers.get("X-API-Key", "")
    if configured_key and not secrets.compare_digest(configured_key, supplied_key):
        return jsonify(success=False, error="Invalid API key"), 401

    url = request.args.get("url", "").strip()
    quality = request.args.get("quality", "best").lower()
    if not url:
        return home()
    if len(url) > 2048 or quality not in QUALITIES:
        return jsonify(success=False, error="Invalid URL length or quality"), 400
    if not platform_from_url(url):
        return jsonify(success=False, error="Unsupported video URL"), 400

    try:
        return jsonify(get_video(url, quality))
    except (ValueError, DownloadError) as exc:
        return jsonify(
            success=False,
            error="ভিডিও পাওয়া যায়নি। এটি private, restricted, unavailable বা blocked হতে পারে।",
            detail=str(exc)[:300],
        ), 422
    except Exception:
        app.logger.exception("Video extraction failed")
        return jsonify(success=False, error="Server error; Vercel logs দেখুন।"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
