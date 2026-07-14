"""Alibaba Cloud Model Studio HappyHorse image-to-video provider."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


REGION_BASE_URLS = {
    "beijing": "https://dashscope.aliyuncs.com/api/v1",
    "singapore": "https://dashscope-intl.aliyuncs.com/api/v1",
}


class HappyHorseVideo(BaseTool):
    name = "happyhorse_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "dashscope_happyhorse"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.ASYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set DASHSCOPE_API_KEY to an Alibaba Cloud Model Studio API key and "
        "DASHSCOPE_REGION to beijing or singapore. The key, model, and endpoint "
        "must belong to the same region."
    )
    fallback_tools = ["grok_video", "wan_video", "ltx_video_local"]
    agent_skills = ["dashscope-media", "ai-video-gen"]

    capabilities = ["image_to_video", "first_frame_video", "model_selection"]
    supports = {
        "text_to_video": False,
        "image_to_video": True,
        "reference_image": True,
        "native_audio": False,
        "seed": True,
        "watermark": True,
    }
    best_for = [
        "short first-frame image-to-video inserts from approved source imagery",
        "3-15 second 720P or 1080P motion shots with reproducible seed metadata",
    ]
    not_good_for = [
        "truth claims that the generated motion itself proves",
        "offline production",
        "native synchronized narration",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "maxLength": 5000},
            "operation": {"type": "string", "enum": ["image_to_video"], "default": "image_to_video"},
            "model": {
                "type": "string",
                "enum": ["happyhorse-1.1-i2v", "happyhorse-1.0-i2v"],
                "default": "happyhorse-1.1-i2v",
            },
            "reference_image_path": {"type": "string"},
            "reference_image_url": {"type": "string"},
            "image_path": {"type": "string"},
            "image_url": {"type": "string"},
            "resolution": {"type": "string", "enum": ["720P", "1080P"], "default": "720P"},
            "duration": {"type": "integer", "minimum": 3, "maximum": 15, "default": 3},
            "watermark": {"type": "boolean", "default": True},
            "seed": {"type": "integer", "minimum": 0, "maximum": 2147483647},
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
            "transport": {
                "type": "string",
                "enum": ["requests", "curl-http1"],
                "default": "requests",
                "description": "Use curl-http1 when the regional endpoint closes or stalls Python HTTP uploads.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout", "rate_limit"])
    idempotency_key_fields = ["prompt", "model", "duration", "resolution", "seed"]
    side_effects = [
        "creates a billable asynchronous DashScope video task",
        "writes video and redacted provider metadata files",
    ]
    user_visible_verification = [
        "Watch the full clip for geometry drift, subject deformation, and prompt fidelity",
        "Verify generated motion is disclosed when factual source truth matters",
    ]
    quality_score = 0.84
    latency_p50_seconds = 180.0

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if os.environ.get("DASHSCOPE_API_KEY") else ToolStatus.UNAVAILABLE

    @staticmethod
    def _region(inputs: dict[str, Any]) -> str:
        return str(inputs.get("region") or os.environ.get("DASHSCOPE_REGION") or "beijing").lower()

    def _base_url(self, inputs: dict[str, Any]) -> str:
        explicit = inputs.get("base_url") or os.environ.get("DASHSCOPE_BASE_URL")
        if explicit:
            return str(explicit).rstrip("/")
        region = self._region(inputs)
        if region not in REGION_BASE_URLS:
            raise ValueError(f"Unsupported DashScope region: {region}")
        return REGION_BASE_URLS[region]

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        duration = int(inputs.get("duration", 3))
        resolution = str(inputs.get("resolution", "720P")).upper()
        region = self._region(inputs)
        if region == "singapore":
            rate = 0.14 if resolution == "720P" else 0.18
        else:
            rate = 0.123769 if resolution == "720P" else 0.165026
        return round(rate * duration, 6)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 180.0

    @staticmethod
    def _image_data_uri(path_value: str) -> str:
        path = Path(path_value).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"First-frame image not found: {path}")
        if path.stat().st_size > 20 * 1024 * 1024:
            raise ValueError("First-frame image exceeds the 20 MB provider limit")
        mime, _ = mimetypes.guess_type(path.name)
        if mime not in {"image/jpeg", "image/png", "image/webp"}:
            raise ValueError("First-frame image must be JPEG, PNG, or WEBP")
        try:
            from PIL import Image

            with Image.open(path) as image:
                width, height = image.size
            if width < 300 or height < 300:
                raise ValueError("First-frame width and height must both be at least 300 pixels")
            ratio = width / height
            if not 0.4 <= ratio <= 2.5:
                raise ValueError("First-frame aspect ratio must be between 1:2.5 and 2.5:1")
        except ImportError:
            pass
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def _image_ref(self, inputs: dict[str, Any]) -> str:
        url = inputs.get("reference_image_url") or inputs.get("image_url")
        if url:
            return str(url)
        path = inputs.get("reference_image_path") or inputs.get("image_path")
        if path:
            return self._image_data_uri(str(path))
        raise ValueError("image_to_video requires reference_image_path or reference_image_url")

    def _payload(self, inputs: dict[str, Any]) -> dict[str, Any]:
        duration = int(inputs.get("duration", 3))
        if not 3 <= duration <= 15:
            raise ValueError("HappyHorse duration must be between 3 and 15 seconds")
        resolution = str(inputs.get("resolution", "720P")).upper()
        if resolution not in {"720P", "1080P"}:
            raise ValueError("HappyHorse resolution must be 720P or 1080P")
        parameters: dict[str, Any] = {
            "resolution": resolution,
            "duration": duration,
            "watermark": bool(inputs.get("watermark", True)),
        }
        if inputs.get("seed") is not None:
            parameters["seed"] = int(inputs["seed"])
        return {
            "model": inputs.get("model", "happyhorse-1.1-i2v"),
            "input": {
                "prompt": inputs["prompt"],
                "media": [{"type": "first_frame", "url": self._image_ref(inputs)}],
            },
            "parameters": parameters,
        }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            return ToolResult(success=False, error="No DashScope API key. " + self.install_instructions)

        import requests
        from tools.video._shared import probe_output

        start = time.time()
        task_id: str | None = str(inputs.get("resume_task_id") or "") or None
        data: dict[str, Any] = {}
        output_path = Path(inputs.get("output_path", "happyhorse_video_output.mp4"))
        metadata_path = Path(
            inputs.get("metadata_path") or output_path.with_suffix(output_path.suffix + ".json")
        )
        try:
            base_url = self._base_url(inputs)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            }
            if not task_id:
                submit_url = f"{base_url}/services/aigc/video-generation/video-synthesis"
                if inputs.get("transport") == "curl-http1":
                    status_code, data = self._post_curl_http1(
                        url=submit_url,
                        api_key=api_key,
                        payload=self._payload(inputs),
                    )
                else:
                    response = requests.post(
                        submit_url,
                        headers=headers,
                        json=self._payload(inputs),
                        # Base64 first-frame uploads can exceed the default connect/write
                        # window on slower routes even when the image is provider-valid.
                        timeout=(60, 90),
                    )
                    status_code = response.status_code
                    data = self._response_json(response)
                task_id = (data.get("output") or {}).get("task_id")
                if status_code >= 400 or not task_id:
                    raise RuntimeError(self._provider_error(status_code, data))

            # Persist the recovery handle before the first poll. A network failure
            # after task creation must never force a duplicate billable submit.
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(
                json.dumps(
                    {
                        "provider": self.provider,
                        "model": inputs.get("model", "happyhorse-1.1-i2v"),
                        "region": self._region(inputs),
                        "task_id": task_id,
                        "request_id": data.get("request_id"),
                        "status": (data.get("output") or {}).get("task_status", "PENDING"),
                        "resumed": bool(inputs.get("resume_task_id")),
                        "seed": inputs.get("seed"),
                        "resolution": str(inputs.get("resolution", "720P")).upper(),
                        "duration": int(inputs.get("duration", 3)),
                        "watermark": bool(inputs.get("watermark", True)),
                        "transport": str(inputs.get("transport", "requests")),
                        "cost_usd_estimate": self.estimate_cost(inputs),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            deadline = time.time() + int(inputs.get("timeout_seconds", 600))
            poll_interval = float(inputs.get("poll_interval_seconds", 15))
            result_data: dict[str, Any] = {}
            while time.time() < deadline:
                try:
                    poll = requests.get(
                        f"{base_url}/tasks/{task_id}",
                        headers={"Authorization": f"Bearer {api_key}"},
                        timeout=(60, 90),
                    )
                except requests.RequestException:
                    # The native DashScope route is intermittently lossy on this
                    # host. Once a task ID exists, retry polling only; never submit
                    # another billable generation request.
                    time.sleep(poll_interval)
                    continue
                result_data = self._response_json(poll)
                output = result_data.get("output") or {}
                status = output.get("task_status")
                if status == "SUCCEEDED":
                    break
                if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                    raise RuntimeError(
                        f"task {status}: {output.get('code') or ''} {output.get('message') or ''}".strip()
                    )
                time.sleep(poll_interval)
            else:
                raise RuntimeError("HappyHorse task timed out")

            output = result_data.get("output") or {}
            video_url = output.get("video_url")
            if not video_url:
                raise RuntimeError("HappyHorse task succeeded without video_url")
            download = requests.get(video_url, timeout=(10, 300))
            download.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(download.content)

            metadata = {
                "provider": self.provider,
                "model": inputs.get("model", "happyhorse-1.1-i2v"),
                "region": self._region(inputs),
                "task_id": task_id,
                "request_id": result_data.get("request_id") or data.get("request_id"),
                "status": output.get("task_status"),
                "usage": result_data.get("usage"),
                "seed": inputs.get("seed"),
                "resolution": str(inputs.get("resolution", "720P")).upper(),
                "duration": int(inputs.get("duration", 3)),
                "watermark": bool(inputs.get("watermark", True)),
                "transport": str(inputs.get("transport", "requests")),
                "cost_usd_estimate": self.estimate_cost(inputs),
            }
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            probed = probe_output(output_path)
        except Exception as exc:
            return ToolResult(
                success=False,
                error=f"{self.name} generation failed: {exc}",
                data={
                    "task_id": task_id,
                    "recoverable_task": bool(task_id),
                    "metadata_path": str(metadata_path) if metadata_path.exists() else None,
                },
            )

        return ToolResult(
            success=True,
            data={**metadata, **probed, "output": str(output_path), "metadata_path": str(metadata_path)},
            artifacts=[str(output_path), str(metadata_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=str(inputs.get("model", "happyhorse-1.1-i2v")),
        )

    @staticmethod
    def _response_json(response: Any) -> dict[str, Any]:
        try:
            return response.json()
        except Exception as exc:
            raise RuntimeError(f"HTTP {response.status_code} returned non-JSON output") from exc

    @staticmethod
    def _provider_error(status_code: int, data: dict[str, Any]) -> str:
        code = data.get("code") or (data.get("output") or {}).get("code") or "provider_error"
        message = data.get("message") or (data.get("output") or {}).get("message") or "unknown error"
        return f"HTTP {status_code}: {code}: {message}"

    @staticmethod
    def _post_curl_http1(
        *, url: str, api_key: str, payload: dict[str, Any]
    ) -> tuple[int, dict[str, Any]]:
        """Submit the base64 image through curl without exposing the API key."""
        header_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", prefix="openmontage-happyhorse-", suffix=".headers", delete=False
            ) as headers:
                header_path = Path(headers.name)
                os.chmod(header_path, 0o600)
                headers.write(f"Authorization: Bearer {api_key}\n")
                headers.write("Content-Type: application/json\n")
                headers.write("X-DashScope-Async: enable\n")
            result = subprocess.run(
                [
                    "curl", "--http1.1", "--silent", "--show-error",
                    "--connect-timeout", "60", "--max-time", "180",
                    "--request", "POST", "--header", f"@{header_path}",
                    "--data-binary", "@-", "--write-out", "\n%{http_code}", url,
                ],
                input=json.dumps(payload), text=True, capture_output=True, check=False,
            )
            if result.returncode:
                raise RuntimeError(
                    f"curl HTTP/1.1 transport failed with exit {result.returncode}: {result.stderr[-300:]}"
                )
            body, _, status = result.stdout.rpartition("\n")
            try:
                return int(status), json.loads(body)
            except (ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("curl HTTP/1.1 returned an invalid provider response") from exc
        finally:
            if header_path:
                header_path.unlink(missing_ok=True)
