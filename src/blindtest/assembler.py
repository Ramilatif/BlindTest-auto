"""Blind test assembly utilities."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence


class AssemblyError(RuntimeError):
    """Raised when the blind test cannot be assembled."""


def _load_moviepy():
    try:
        from moviepy.editor import (
            AudioClip,
            AudioFileClip,
            ColorClip,
            VideoFileClip,
            concatenate_audioclips,
            concatenate_videoclips,
        )
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise AssemblyError(
            "moviepy is required to assemble the blind test. Install it with 'pip install moviepy'."
        ) from exc
    return (
        AudioClip,
        AudioFileClip,
        ColorClip,
        VideoFileClip,
        concatenate_audioclips,
        concatenate_videoclips,
    )


def build_blindtest(
    clips: Sequence[Path],
    *,
    output_path: str | Path = "blindtest.mp4",
    silence_duration: float = 1.0,
    audio_only: bool = False,
) -> Path:
    """Concatenate *clips* with optional silent transitions to build the final file."""

    if not clips:
        raise AssemblyError("No clips were provided for assembly")

    if silence_duration < 0:
        raise AssemblyError("silence_duration must be zero or greater")

    (
        AudioClip,
        AudioFileClip,
        ColorClip,
        VideoFileClip,
        concatenate_audioclips,
        concatenate_videoclips,
    ) = _load_moviepy()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    assembled_clips: List = []

    for clip_path in clips:
        if audio_only:
            media_clip = AudioFileClip(str(clip_path))
            assembled_clips.append(media_clip)
            if silence_duration:
                silence = AudioClip(lambda t: 0, duration=silence_duration)
                assembled_clips.append(silence)
        else:
            media_clip = VideoFileClip(str(clip_path))
            assembled_clips.append(media_clip)
            if silence_duration:
                silence = ColorClip(size=media_clip.size, color=(0, 0, 0), duration=silence_duration)
                silence = silence.set_audio(AudioClip(lambda t: 0, duration=silence_duration))
                assembled_clips.append(silence)

    if audio_only:
        final_clip = concatenate_audioclips(assembled_clips)
        final_clip.write_audiofile(str(output_path), verbose=False, logger=None)
    else:
        final_clip = concatenate_videoclips(assembled_clips, method="compose")
        final_clip.write_videofile(str(output_path), audio=True, verbose=False, logger=None)

    for clip in assembled_clips:
        clip.close()

    final_clip.close()

    return output_path


__all__ = ["build_blindtest", "AssemblyError"]
