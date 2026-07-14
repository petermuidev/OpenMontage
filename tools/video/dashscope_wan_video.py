"""Low-cost DashScope Wan image-to-video provider."""

from __future__ import annotations

from typing import Any

from tools.base_tool import ToolResult
from tools.video.happyhorse_video import HappyHorseVideo


class DashScopeWanVideo(HappyHorseVideo):
    """Wan 2.6 Flash I2V using the same native async transport as HappyHorse."""

    name = "dashscope_wan_video"
    version = "0.1.0"
    provider = "dashscope_wan"
    fallback_tools = ["happyhorse_video", "grok_video", "wan_video", "ltx_video_local"]
    agent_skills = ["dashscope-media", "ai-video-gen"]

    capabilities = ["image_to_video", "first_frame_video", "low_cost_video"]
    supports = {
        "text_to_video": False,
        "image_to_video": True,
        "reference_image": True,
        "native_audio": False,
        "silent_video": True,
        "seed": True,
        "watermark": True,
    }
    best_for = [
        "low-cost locked-camera animation of approved still imagery",
        "silent 2-15 second layers composed later with cuts, captions, music, or narration",
    ]
    not_good_for = [
        "standalone hero shots where motion quality is the main selling point",
        "native synchronized narration",
        "truth claims that generated motion itself proves",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "maxLength": 1500},
            "negative_prompt": {"type": "string", "maxLength": 500},
            "operation": {"type": "string", "enum": ["image_to_video"], "default": "image_to_video"},
            "model": {"type": "string", "enum": ["wan2.6-i2v-flash"], "default": "wan2.6-i2v-flash"},
            "reference_image_path": {"type": "string"},
            "reference_image_url": {"type": "string"},
            "image_path": {"type": "string"},
            "image_url": {"type": "string"},
            "resolution": {"type": "string", "enum": ["720P", "1080P"], "default": "720P"},
            "duration": {"type": "integer", "minimum": 2, "maximum": 15, "default": 2},
            "watermark": {"type": "boolean", "default": True},
            "seed": {"type": "integer", "minimum": 0, "maximum": 2147483647},
            "prompt_extend": {"type": "boolean", "default": False},
            "region": {"type": "string", "enum": ["beijing", "singapore"]},
            "base_url": {"type": "string"},
            "output_path": {"type": "string"},
            "metadata_path": {"type": "string"},
            "resume_task_id": {
                "type": "string",
                "description": "Resume polling an accepted task without creating another billable task.",
            },
            "poll_interval_seconds": {"type": "number", "minimum": 2, "default": 15},
            "timeout_seconds": {"type": "integer", "minimum": 30, "default": 600},
            "transport": {"type": "string", "enum": ["requests", "curl-http1"], "default": "requests"},
        },
    }

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        duration = int(inputs.get("duration", 2))
        resolution = str(inputs.get("resolution", "720P")).upper()
        region = self._region(inputs)
        if region == "singapore":
            rate = 0.025 if resolution == "720P" else 0.0375
        else:
            rate = 0.021503 if resolution == "720P" else 0.035838
        return round(rate * duration, 6)

    def _payload(self, inputs: dict[str, Any]) -> dict[str, Any]:
        duration = int(inputs.get("duration", 2))
        if not 2 <= duration <= 15:
            raise ValueError("Wan 2.6 Flash duration must be between 2 and 15 seconds")
        resolution = str(inputs.get("resolution", "720P")).upper()
        if resolution not in {"720P", "1080P"}:
            raise ValueError("Wan 2.6 Flash resolution must be 720P or 1080P")
        input_data: dict[str, Any] = {
            "prompt": inputs["prompt"],
            "img_url": self._image_ref(inputs),
        }
        if inputs.get("negative_prompt"):
            input_data["negative_prompt"] = str(inputs["negative_prompt"])
        parameters: dict[str, Any] = {
            "resolution": resolution,
            "duration": duration,
            "audio": False,
            "prompt_extend": bool(inputs.get("prompt_extend", False)),
            "watermark": bool(inputs.get("watermark", True)),
        }
        if inputs.get("seed") is not None:
            parameters["seed"] = int(inputs["seed"])
        return {
            "model": "wan2.6-i2v-flash",
            "input": input_data,
            "parameters": parameters,
        }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        normalized = dict(inputs)
        normalized.setdefault("model", "wan2.6-i2v-flash")
        normalized.setdefault("duration", 2)
        normalized.setdefault("resolution", "720P")
        return super().execute(normalized)
