"""Command line entry point to build a blind test from YouTube videos."""
from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

from .assembler import AssemblyError, build_blindtest
from .clipper import ClipGenerationError, clip_videos
from .video_sources import VideoRetrievalError, fetch_video_clips


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
LOGGER = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="YouTube search query or playlist name")
    parser.add_argument("--max-results", type=int, default=5, help="Number of clips to fetch")
    parser.add_argument("--clip-duration", type=float, default=10.0, help="Length of each clip in seconds")
    parser.add_argument("--output", default="blindtest.mp4", help="Path to the final blind test file")
    parser.add_argument("--downloads", default="downloads", help="Directory where raw downloads are stored")
    parser.add_argument("--clips", default="clips", help="Directory to store intermediate clips")
    parser.add_argument("--no-random", action="store_true", help="Do not randomize clip order")
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Generate an audio-only blind test",
    )
    parser.add_argument(
        "--silence-duration",
        type=float,
        default=1.0,
        help="Duration of the silent transition between clips",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    download_dir = Path(args.downloads)
    clips_dir = Path(args.clips)

    try:
        LOGGER.info("Fetching videos matching '%s'", args.query)
        videos = fetch_video_clips(
            args.query,
            max_results=args.max_results,
            download_dir=download_dir,
            randomize=not args.no_random,
        )

        LOGGER.info("Generating %s clips", len(videos))
        generated_clips = clip_videos(
            videos,
            clip_duration=args.clip_duration,
            output_dir=clips_dir,
            audio_only=args.audio_only,
        )

        LOGGER.info("Assembling blind test into %s", args.output)
        build_blindtest(
            generated_clips,
            output_path=args.output,
            silence_duration=args.silence_duration,
            audio_only=args.audio_only,
        )
        LOGGER.info("Blind test created successfully!")
        return 0
    except (VideoRetrievalError, ClipGenerationError, AssemblyError) as exc:
        LOGGER.error("%s", exc)
        return 1
    finally:
        if download_dir.exists():
            shutil.rmtree(download_dir)
        if clips_dir.exists():
            shutil.rmtree(clips_dir)


if __name__ == "__main__":
    sys.exit(main())
