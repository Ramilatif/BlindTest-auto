"""Utilities for retrieving and downloading video clips from YouTube."""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

try:  # pragma: no cover - fallback exercised in environments without requests
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    requests = None  # type: ignore


YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"


class VideoRetrievalError(RuntimeError):
    """Raised when video clips cannot be retrieved or downloaded."""


@dataclass
class VideoClip:
    """Representation of a YouTube clip that was downloaded locally."""

    video_id: str
    title: str
    url: str
    file_path: Path


def _download_video(video_id: str, target_dir: Path) -> Path:
    """Download the YouTube video with *video_id* into *target_dir*.

    The function attempts to use :mod:`pytube` first and falls back to
    :mod:`youtube_dl` if available. The download is limited to the audio stream
    to keep the footprint small. A :class:`VideoRetrievalError` is raised if no
    downloader is available.
    """

    target_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    file_path = target_dir / f"{video_id}.mp4"

    # Delay imports until runtime to keep optional dependencies optional during
    # unit tests. This avoids requiring heavy libraries for simple validations.
    try:
        from pytube import YouTube  # type: ignore
    except ModuleNotFoundError:
        YouTube = None  # type: ignore

    if YouTube is not None:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        if stream is None:
            raise VideoRetrievalError(f"No audio stream available for {video_id}")
        stream.download(output_path=str(target_dir), filename=file_path.name)
        return file_path

    try:
        import youtube_dl  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - executed when missing dependency
        raise VideoRetrievalError(
            "Neither pytube nor youtube_dl is available to download videos."
        ) from exc

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(file_path),
        "quiet": True,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:  # type: ignore[attr-defined]
        ydl.download([url])
    return file_path


def _build_search_params(
    query: str,
    *,
    api_key: str,
    max_results: int,
    published_after: Optional[str] = None,
) -> dict:
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": max_results,
        "type": "video",
        "key": api_key,
        "videoEmbeddable": "true",
    }
    if published_after:
        params["publishedAfter"] = published_after
    return params


def _call_youtube_api(params: dict) -> dict:
    if requests is None:  # pragma: no cover - depends on optional dependency
        raise VideoRetrievalError(
            "The 'requests' package is required to call the YouTube API. Install it with 'pip install requests'."
        )
    response = requests.get(YOUTUBE_API_URL, params=params, timeout=10)
    if response.status_code != 200:
        raise VideoRetrievalError(
            f"YouTube API request failed with status {response.status_code}: {response.text}"
        )
    return response.json()


def fetch_video_clips(
    query: str,
    *,
    max_results: int = 5,
    api_key: Optional[str] = None,
    download_dir: str | Path = "downloads",
    published_after: Optional[str] = None,
    randomize: bool = True,
) -> List[VideoClip]:
    """Retrieve and download a list of YouTube videos matching *query*.

    Parameters
    ----------
    query:
        Keyword or playlist search string used in the YouTube Data API.
    max_results:
        Maximum number of items to download.
    api_key:
        YouTube Data API key. If omitted, the value from the
        ``YOUTUBE_API_KEY`` environment variable is used.
    download_dir:
        Directory where downloaded files will be stored.
    published_after:
        ISO timestamp used to filter recent videos.
    randomize:
        When ``True`` the resulting list will be shuffled before being returned.
    """

    api_key = api_key or os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise VideoRetrievalError(
            "A YouTube API key must be supplied via the api_key argument or the "
            "YOUTUBE_API_KEY environment variable."
        )

    params = _build_search_params(
        query,
        api_key=api_key,
        max_results=max_results,
        published_after=published_after,
    )

    data = _call_youtube_api(params)
    items = data.get("items", [])
    if not items:
        raise VideoRetrievalError("No videos were returned by the YouTube API")

    clips: List[VideoClip] = []
    download_path = Path(download_dir)

    for item in items:
        video_id = item["id"].get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue
        title = snippet.get("title", "Untitled")
        url = f"https://www.youtube.com/watch?v={video_id}"

        file_path = _download_video(video_id, download_path)
        clips.append(VideoClip(video_id=video_id, title=title, url=url, file_path=file_path))

        # Sleep a bit to avoid triggering quota limits for rapid downloads.
        time.sleep(0.1)

    if randomize:
        random.shuffle(clips)

    return clips


__all__ = [
    "VideoClip",
    "VideoRetrievalError",
    "fetch_video_clips",
]
