from pathlib import Path
from unittest import mock

from blindtest import assembler


class DummyClip:
    def __init__(self, name, size=(640, 480)):
        self.name = name
        self.size = size
        self.duration = 5

    def set_audio(self, audio):
        return self

    def close(self):
        pass


class DummyConcat:
    def __init__(self, clips):
        self.clips = clips

    def write_videofile(self, *_args, **_kwargs):
        pass

    def write_audiofile(self, *_args, **_kwargs):
        pass

    def close(self):
        pass


def test_build_blindtest_keeps_order(tmp_path):
    created = {}

    def fake_loader():
        def audio_clip(_func, duration):
            return DummyClip(f"silence-{duration}")

        def audio_file_clip(path):
            return DummyClip(Path(path).stem)

        def color_clip(size, color, duration):
            return DummyClip(f"color-{duration}", size=size)

        def video_file_clip(path):
            return DummyClip(Path(path).stem)

        def concat_audio(clips):
            created["audio"] = clips
            return DummyConcat(clips)

        def concat_video(clips, method=None):
            created["video"] = clips
            return DummyConcat(clips)

        return audio_clip, audio_file_clip, color_clip, video_file_clip, concat_audio, concat_video

    with mock.patch.object(assembler, "_load_moviepy", side_effect=fake_loader):
        clip_paths = [tmp_path / f"clip_{i}.mp4" for i in range(3)]
        for path in clip_paths:
            path.write_text("data")
        output = assembler.build_blindtest(clip_paths, output_path=tmp_path / "final.mp4")

    assert output == tmp_path / "final.mp4"
    ordered_names = [clip.name for clip in created["video"]]
    assert ordered_names[0::2] == [f"clip_{i}" for i in range(3)]
