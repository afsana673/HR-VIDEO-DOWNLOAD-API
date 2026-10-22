"""HR Video Downloader — video metadata and direct media links (not a video proxy)."""
import json
import os
import secrets
import shutil
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit

import yt_dlp
from yt_dlp.utils import DownloadError

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


def platform_from_url(raw_url):
    try:
        parts = urlsplit(raw_url.strip())
        host = (parts.hostname or "").lower().rstrip(".")
        if parts.scheme not in ("http", "https") or not host:
            return None
        if parts.username or parts.password or (parts.port not in (None, 80, 443)):
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
    # YouTube's player challenges may require Node 22+ or Deno and yt-dlp-ejs.
    # If Vercel has no supported JS runtime, some YouTube URLs will fail.
    if shutil.which("node"):
        options["js_runtimes"] = {"node": {}}

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise ValueError("ভিডিওর তথ্য পাওয়া যায়নি।")
    if info.get("_type") in ("playlist", "multi_video"):
        entries = [x for x in (info.get("entries") or []) if x]
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
        # Never claim video-only formats are complete downloads with sound.
        if fmt.get("vcodec") == "none" or fmt.get("acodec") == "none":
            continue
        candidates.append(fmt)

    if not candidates:
        raise ValueError(
            "সরাসরি MP4/WebM (ভিডিও+অডিও) লিংক পাওয়া যায়নি। "
            "এই ভিডিওর জন্য আলাদা audio/video merge বা login লাগতে পারে।"
        )

    # Prefer requested resolution first, then MP4 when quality is equal.
    if quality == "best":
        chosen = max(candidates, key=lambda x: (
            x.get("height") or 0, x.get("ext") == "mp4", x.get("tbr") or 0
        ))
    else:
        limit = int(quality)
        below = [f for f in candidates if (f.get("height") or 0) <= limit]
        chosen = (max(below, key=lambda x: (
            x.get("height") or 0, x.get("ext") == "mp4", x.get("tbr") or 0
        )) if below else min(candidates, key=lambda x: (
            x.get("height") or 99999, x.get("ext") != "mp4"
        )))

    found = [f"{h}p" for h in sorted({int(f["height"]) for f in candidates if f.get("height")})]
    headers = chosen.get("http_headers") or info.get("http_headers") or {}
    safe_headers = {
        k: v for k, v in headers.items()
        if k.lower() in ("user-agent", "referer", "origin") and isinstance(v, str)
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
        "available_qualities": found,
        "extension": chosen.get("ext"),
        "download_url": chosen["url"],
        "request_headers": safe_headers,
        "note": "লিংকটি অস্থায়ী হতে পারে; কিছু CDN-এ বিশেষ headers/IP প্রয়োজন হয়।",
    }


class handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.respond(200, {"success": True})

    def do_GET(self):
        params = parse_qs(urlsplit(self.path).query)
        url = (params.get("url") or [""])[0].strip()
        quality = (params.get("quality") or ["best"])[0].lower()
        configured_key = os.environ.get("DOWNLOAD_API_KEY") or ""
        supplied_key = self.headers.get("X-API-Key") or ""

        if configured_key and not secrets.compare_digest(configured_key, supplied_key):
            return self.respond(401, {"success": False, "error": "Invalid API key"})
        if not url:
            return self.respond(200, {
                "success": True, "api": "HR VIDEO DOWNLOADER",
                "usage": "/api/download?url=VIDEO_URL&quality=best",
                "qualities": ["best", "360", "480", "720", "1080"],
                "platforms": list(HOSTS),
            })
        if len(url) > 2048 or quality not in {"best", "360", "480", "720", "1080"}:
            return self.respond(400, {"success": False, "error": "Invalid URL length or quality"})
        if not platform_from_url(url):
            return self.respond(400, {"success": False, "error": "Unsupported video URL"})
        try:
            return self.respond(200, get_video(url, quality))
        except (ValueError, DownloadError) as exc:
            return self.respond(422, {
                "success": False,
                "error": "ভিডিও পাওয়া যায়নি। এটি private, restricted, unavailable বা blocked হতে পারে।",
                "detail": str(exc)[:300],
            })
        except Exception:
            return self.respond(500, {"success": False, "error": "Server error; Vercel logs দেখুন।"})
