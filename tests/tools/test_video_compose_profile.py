"""Regression coverage for profile-aware FFmpeg segment normalization."""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from tools.video.video_compose import VideoCompose


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="ffmpeg and ffprobe are required",
)
def test_compose_preserves_tiktok_vertical_profile(tmp_path):
    source = tmp_path / "source.mp4"
    output = tmp_path / "output.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "color=c=blue:s=1080x1920:r=30:d=0.5",
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-t", "0.5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(source),
        ],
        check=True,
    )

    result = VideoCompose().execute(
        {
            "operation": "compose",
            "profile": "tiktok",
            "edit_decisions": {
                "cuts": [
                    {"source": str(source), "in_seconds": 0, "out_seconds": 0.5}
                ]
            },
            "output_path": str(output),
        }
    )

    assert result.success, result.error
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json", str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    stream = json.loads(probe.stdout)["streams"][0]
    assert (stream["width"], stream["height"]) == (1080, 1920)
