from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from tools.audio.qwen_tts import QwenTTS
from tools.base_tool import ToolStatus
from tools.video.dashscope_wan_video import DashScopeWanVideo
from tools.video.happyhorse_video import HappyHorseVideo


def test_dashscope_tools_require_key(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    assert QwenTTS().get_status() == ToolStatus.UNAVAILABLE
    assert DashScopeWanVideo().get_status() == ToolStatus.UNAVAILABLE
    assert HappyHorseVideo().get_status() == ToolStatus.UNAVAILABLE


def test_happyhorse_minimum_beijing_cost():
    assert HappyHorseVideo().estimate_cost({"duration": 3, "resolution": "720P", "region": "beijing"}) == 0.371307


def test_happyhorse_minimum_singapore_cost():
    assert HappyHorseVideo().estimate_cost({"duration": 3, "resolution": "720P", "region": "singapore"}) == 0.42


def test_dashscope_wan_minimum_beijing_cost():
    assert DashScopeWanVideo().estimate_cost(
        {"duration": 2, "resolution": "720P", "region": "beijing"}
    ) == 0.043006


def test_dashscope_wan_silent_payload(tmp_path):
    image_path = tmp_path / "first.jpg"
    Image.new("RGB", (720, 1280), "blue").save(image_path)
    payload = DashScopeWanVideo()._payload(
        {
            "prompt": "Preserve geometry. Add subtle water motion.",
            "negative_prompt": "people, text, new objects",
            "reference_image_path": str(image_path),
            "duration": 2,
            "resolution": "720P",
            "seed": 42,
        }
    )
    assert payload["model"] == "wan2.6-i2v-flash"
    assert payload["input"]["img_url"].startswith("data:image/jpeg;base64,")
    assert payload["input"]["negative_prompt"] == "people, text, new objects"
    assert payload["parameters"] == {
        "resolution": "720P",
        "duration": 2,
        "audio": False,
        "prompt_extend": False,
        "watermark": True,
        "seed": 42,
    }


def test_happyhorse_payload_uses_first_frame_data_uri(tmp_path):
    image_path = tmp_path / "first.png"
    Image.new("RGB", (720, 1280), "blue").save(image_path)
    payload = HappyHorseVideo()._payload(
        {
            "prompt": "Preserve geometry. Add subtle ocean movement.",
            "reference_image_path": str(image_path),
            "duration": 3,
            "resolution": "720P",
            "seed": 42,
        }
    )
    assert payload["model"] == "happyhorse-1.1-i2v"
    assert payload["input"]["media"][0]["type"] == "first_frame"
    assert payload["input"]["media"][0]["url"].startswith("data:image/png;base64,")
    assert payload["parameters"] == {
        "resolution": "720P",
        "duration": 3,
        "watermark": True,
        "seed": 42,
    }


def test_happyhorse_rejects_too_small_first_frame(tmp_path):
    image_path = tmp_path / "small.png"
    Image.new("RGB", (299, 600), "blue").save(image_path)
    try:
        HappyHorseVideo()._image_data_uri(str(image_path))
    except ValueError as exc:
        assert "at least 300" in str(exc)
    else:
        raise AssertionError("small image should be rejected")


def test_qwen_cost_is_character_based():
    assert QwenTTS().estimate_cost({"text": "x" * 100, "region": "beijing"}) == 0.001147


def test_qwen_instruct_payload(monkeypatch, tmp_path):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-secret")
    post_response = Mock(status_code=200)
    post_response.json.return_value = {
        "request_id": "request-voice",
        "output": {"audio": {"url": "https://example.invalid/voice.wav", "id": "audio-1"}},
        "usage": {"characters": 11},
    }
    download = Mock(content=b"voice")
    download.raise_for_status.return_value = None
    with patch("requests.post", return_value=post_response) as post, patch(
        "requests.get", return_value=download
    ), patch("tools.analysis.audio_probe.probe_duration", return_value=1.0):
        result = QwenTTS().execute(
            {
                "text": "Begin now.",
                "model": "qwen3-tts-instruct-flash",
                "voice": "Ryan",
                "language_type": "English",
                "instructions": "Warm motivational speaker, measured pace.",
                "output_path": str(tmp_path / "voice.wav"),
            }
        )
    assert result.success
    sent = post.call_args.kwargs["json"]
    assert sent["input"]["instructions"].startswith("Warm motivational")
    assert sent["input"]["optimize_instructions"] is True


def test_qwen_downloads_audio_and_writes_redacted_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-secret")
    output = tmp_path / "voice.wav"
    post_response = Mock(status_code=200)
    post_response.json.return_value = {
        "request_id": "request-1",
        "output": {
            "audio": {
                "url": "https://example.invalid/signed.wav?secret=yes",
                "id": "audio-1",
                "expires_at": 123,
            }
        },
        "usage": {"characters": 14},
    }
    get_response = Mock(content=b"fake-wav")
    get_response.raise_for_status.return_value = None
    with patch("requests.post", return_value=post_response), patch(
        "requests.get", return_value=get_response
    ), patch("tools.analysis.audio_probe.probe_duration", return_value=1.2):
        result = QwenTTS().execute(
            {
                "text": "Samui in motion.",
                "voice": "Jennifer",
                "language_type": "English",
                "output_path": str(output),
            }
        )
    assert result.success
    assert output.read_bytes() == b"fake-wav"
    metadata = Path(result.data["metadata_path"]).read_text()
    assert "request-1" in metadata
    assert "signed.wav" not in metadata
    assert "test-secret" not in metadata


def test_registry_discovers_dashscope_providers():
    from tools.tool_registry import ToolRegistry

    registry = ToolRegistry()
    registry.discover()
    assert registry.get("dashscope_wan_video").provider == "dashscope_wan"
    assert registry.get("happyhorse_video").provider == "dashscope_happyhorse"
    assert registry.get("qwen_tts").provider == "dashscope_qwen"


def test_qwen_curl_transport_keeps_key_out_of_argv(monkeypatch):
    recorded = {}

    def fake_run(command, **kwargs):
        recorded["command"] = command
        recorded["input"] = kwargs["input"]
        return Mock(
            returncode=0,
            stdout='{"output":{"audio":{"url":"https://example.invalid/a.wav"}}}\n200',
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    status, payload = QwenTTS._post_curl_http1(
        url="https://example.invalid/generation",
        api_key="secret-test-key",
        payload={"model": "qwen3-tts-flash", "input": {"text": "hello"}},
    )
    assert status == 200
    assert payload["output"]["audio"]["url"].endswith("a.wav")
    assert "secret-test-key" not in " ".join(recorded["command"])
    assert "secret-test-key" not in recorded["input"]


def test_happyhorse_persists_task_before_poll_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-secret")
    image_path = tmp_path / "first.png"
    Image.new("RGB", (720, 1280), "blue").save(image_path)
    output = tmp_path / "clip.mp4"
    submit = Mock(status_code=200)
    submit.json.return_value = {
        "request_id": "request-1",
        "output": {"task_id": "task-1", "task_status": "PENDING"},
    }
    with patch("requests.post", return_value=submit), patch(
        "requests.get", side_effect=TimeoutError("poll failed")
    ):
        result = HappyHorseVideo().execute(
            {
                "prompt": "Preserve geometry. Add subtle water motion.",
                "reference_image_path": str(image_path),
                "duration": 3,
                "resolution": "720P",
                "output_path": str(output),
            }
        )
    assert not result.success
    assert result.data["task_id"] == "task-1"
    assert result.data["recoverable_task"] is True
    metadata = Path(result.data["metadata_path"]).read_text()
    assert "task-1" in metadata
    assert "test-secret" not in metadata


def test_happyhorse_resume_does_not_submit_again(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-secret")
    output = tmp_path / "clip.mp4"
    poll = Mock(status_code=200)
    poll.json.return_value = {
        "request_id": "request-2",
        "output": {"task_id": "task-1", "task_status": "SUCCEEDED", "video_url": "https://example.invalid/clip.mp4"},
        "usage": {"duration": 2},
    }
    download = Mock(content=b"fake-mp4")
    download.raise_for_status.return_value = None
    with patch("requests.post") as submit, patch("requests.get", side_effect=[poll, download]), patch(
        "tools.video._shared.probe_output", return_value={"duration": 2.0}
    ):
        result = HappyHorseVideo().execute(
            {
                "prompt": "unused during resume",
                "resume_task_id": "task-1",
                "duration": 2,
                "resolution": "720P",
                "output_path": str(output),
            }
        )
    assert result.success
    assert output.read_bytes() == b"fake-mp4"
    submit.assert_not_called()


def test_happyhorse_curl_transport_keeps_secret_out_of_argv_and_body(monkeypatch):
    recorded = {}

    def fake_run(command, *, input, text, capture_output, check):
        recorded["command"] = command
        recorded["input"] = input
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"request_id":"r1","output":{"task_id":"t1"}}\n200',
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    status, payload = HappyHorseVideo._post_curl_http1(
        url="https://example.invalid/video-synthesis",
        api_key="secret-happyhorse-key",
        payload={"model": "happyhorse-1.1-i2v", "input": {"prompt": "subtle water"}},
    )
    assert status == 200
    assert payload["output"]["task_id"] == "t1"
    assert "secret-happyhorse-key" not in " ".join(recorded["command"])
    assert "secret-happyhorse-key" not in recorded["input"]
