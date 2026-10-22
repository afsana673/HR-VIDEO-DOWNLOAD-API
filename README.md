<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00F5FF,50:8A2BE2,100:FF1493&height=190&section=header&text=HR%20VIDEO%20DOWNLOADER&fontSize=32&fontColor=FFFFFF&animation=twinkling&desc=Developer%20SK%20HABIBULLA" width="100%" />

# 🌈 HR VIDEO DOWNLOADER 🍘

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=800&size=22&pause=1000&color=FF00FF&center=true&vCenter=true&width=470&lines=DEVELOPER+SK+HABIBULLA;INSTAGRAM+%7C+FACEBOOK;YOUTUBE+%7C+PINTEREST;VERCEL+PYTHON+API" alt="HR video downloader animated title" />

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)
![Facebook](https://img.shields.io/badge/Facebook-0866FF?style=for-the-badge&logo=facebook&logoColor=white)
![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)
![Pinterest](https://img.shields.io/badge/Pinterest-BD081C?style=for-the-badge&logo=pinterest&logoColor=white)
</div>

API for extracting publicly accessible progressive video URLs from Instagram, Facebook, YouTube and Pinterest, using yt-dlp. No media files are transferred through Vercel Functions. Works only where the site's extractor can get metadata without authentication, and browser CDN links may require special HTTP headers / originating IP.

## Files

- `api/index.py` — Vercel Python API function
- `requirements.txt` — required Python package
- `vercel.json` — Vercel function duration and API route rewrite
- `public/index.html` — test page

## Deploy

1. Create a GitHub repository and upload these files preserving their paths.
2. In https://vercel.com/new, import that repository.
3. Framework preset: **Other**. Root directory: `./`. No build command needed.
4. Deploy. Vercel installs `requirements.txt` for the Python function.
5. Open `https://PROJECT.vercel.app/` for the test UI.
6. Open `https://PROJECT.vercel.app/api/download` for API usage.

## API

GET `/api/download?url=ENCODED_VIDEO_URL&quality=best`

- `url`: public video page URL, percent-encoded in the query string
- `quality`: `best`, `360`, `480`, `720`, `1080`
- Returns `download_url` and metadata or an error JSON.

Example (sample URL only; use a real public link):

```js
const params = new URLSearchParams({ url: 'https://www.youtube.com/watch?v=REPLACE_ME', quality: '720' });
const response = await fetch('https://YOUR_PROJECT.vercel.app/api/download?' + params);
const data = await response.json();
console.log(data);
```

## Important limitations

- Vercel has a 4.5 MB function response limit: videos are **not proxied** or assembled.
- Returns only progressive MP4/WebM including audio. It cannot merge separate streams without ffmpeg.
- Some platforms lock media to IP, headers, cookies or time-limited tokens. Returned CDN URLs may not work in browsers.
- YouTube may require a supported JavaScript runtime (Deno, Node 22+) and yt-dlp-ejs; `yt-dlp[default]` installs EJS scripts but Vercel may lack a supported runtime, making YouTube extraction unreliable.
- Platform anti-bot changes and IP blocks can interrupt availability. Protected or private video content is unsupported.
- Optional: set a `DOWNLOAD_API_KEY` Vercel environment variable; API requests must then include `X-API-Key` header. The sample web UI does not expose an API key.
- Only download video you own or have permission to save, in accordance with platform rules and applicable law.

<div align="center">

### 👑 SK HABIBULLA 🍘

**© 2026 HR VIDEO DOWNLOADER**

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:FF1493,50:8A2BE2,100:00F5FF&height=110&section=footer" width="100%" />
</div>
