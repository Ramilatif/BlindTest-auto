from pathlib import Path
from unittest import mock

import pytest

from blindtest import video_sources


@pytest.fixture
def fake_response(tmp_path):
    data = {
        "items": [
            {
                "id": {"videoId": "abc123"},
                "snippet": {"title": "Song 1"},
            },
            {
                "id": {"videoId": "def456"},
                "snippet": {"title": "Song 2"},
            },
        ]
    }

    class DummyResponse:
        status_code = 200

        def json(self):
            return data

    with mock.patch.object(video_sources, "requests") as requests_mock:
        requests_mock.get.return_value = DummyResponse()
        yield


def test_fetch_video_clips_returns_expected_videos(fake_response, tmp_path):
    downloaded_paths = []

    def fake_download(video_id, target_dir):
        path = Path(tmp_path) / f"{video_id}.mp4"
        path.write_text("dummy")
        downloaded_paths.append(path)
        return path

    with mock.patch.object(video_sources, "_download_video", side_effect=fake_download):
        clips = video_sources.fetch_video_clips(
            "test",
            max_results=2,
            api_key="dummy",
            download_dir=tmp_path,
            randomize=False,
        )

    assert [clip.video_id for clip in clips] == ["abc123", "def456"]
    assert all(path.exists() for path in downloaded_paths)
