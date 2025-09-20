"""Clip generation utilities built on top of moviepy."""
from __future__ import annotations

import random
from pathlib import Path
from typing import List, Sequence

from .video_sources import VideoClip


class ClipGenerationError(RuntimeError):
    """Raised when movie segments cannot be generated."""


def _load_moviepy():
    try:
        from moviepy.editor import AudioFileClip, VideoFileClip  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise ClipGenerationError(
            "moviepy is required to generate clips. Install it with 'pip install moviepy'."
        ) from exc
    return AudioFileClip, VideoFileClip


def clip_videos(
    clips: Sequence[VideoClip],
    *,
    clip_duration: float = 10.0,
    output_dir: str | Path = "clips",
    start_strategy: str = "random",
    audio_only: bool = False,
) -> List[Path]:
    """Generate small extracts from the downloaded videos.

    Parameters
    ----------
    clips:
        List of :class:`~blindtest.video_sources.VideoClip` objects describing the
        downloaded videos.
    clip_duration:
        Length of each excerpt in seconds.
    output_dir:
        Directory where generated excerpts are stored.
    start_strategy:
        Either ``"random"`` or ``"start"`` to control how the excerpt position is
        selected.
    audio_only:
        When ``True`` the audio stream is exported instead of a video clip.
    """

    if clip_duration <= 0:
        raise ClipGenerationError("clip_duration must be a positive number")

    AudioFileClip, VideoFileClip = _load_moviepy()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generated_files: List[Path] = []

    for clip in clips:
        source_path = clip.file_path
        if audio_only:
            media_clip = AudioFileClip(str(source_path))
        else:
            media_clip = VideoFileClip(str(source_path))

        duration = media_clip.duration
        if duration is None or duration < clip_duration:
            start = 0
        elif start_strategy == "random":
            start = random.uniform(0, max(0, duration - clip_duration))
        else:
            start = 0

        subclip = media_clip.subclip(start, start + clip_duration)
        target = output_path / f"{clip.video_id}_clip.mp4"
        if audio_only:
            target = target.with_suffix(".mp3")
            subclip.write_audiofile(str(target), verbose=False, logger=None)
        else:
            subclip.write_videofile(str(target), audio=True, verbose=False, logger=None)

        generated_files.append(target)
        media_clip.close()
        subclip.close()

    return generated_files


__all__ = ["clip_videos", "ClipGenerationError"]
