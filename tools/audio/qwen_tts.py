"""Alibaba Cloud Model Studio Qwen3 non-real-time text-to-speech provider."""

from __future__ import annotations

import json
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


class QwenTTS(BaseTool):
    name = "qwen_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "dashscope_qwen"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set DASHSCOPE_API_KEY to an Alibaba Cloud Model Studio API key and "
        "DASHSCOPE_REGION to beijing or singapore. The key, model, and endpoint "
        "must belong to the same region."
    )
    fallback_tools = ["doubao_tts", "openai_tts", "google_tts", "piper_tts"]
    agent_skills = ["dashscope-media", "text-to-speech"]

    capabilities = ["text_to_speech", "voice_selection", "multilingual"]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": False,
        "native_audio": True,
        "timestamps": False,
    }
    best_for = [
        "English narration with a documented built-in voice",
        "short-form commercial and editorial voiceovers",
    ]
    not_good_for = [
        "Thai narration because Qwen3-TTS does not list Thai as a supported language",
        "word-level timing",
        "fully offline production",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string", "maxLength": 600},
            "voice": {"type": "string", "default": "Jennifer"},
            "model": {"type": "string", "default": "qwen3-tts-flash"},
            "instructions": {
                "type": "string",
                "description": "English or Chinese delivery direction for qwen3-tts-instruct-flash.",
            },
            "optimize_instructions": {"type": "boolean", "default": True},
            "language_type": {
                "type": "string",
                "enum": ["Auto", "Chinese", "English", "German", "Italian", "Portuguese", "Spanish", "Japanese", "Korean", "French", "Russian"],
                "default": "English",
            },
            "region": {"type": "string", "enum": ["beijing", "singapore"]},
            "base_url": {"type": "string"},
            "output_path": {"type": "string"},
            "metadata_path": {"type": "string"},
            "transport": {
                "type": "string",
                "enum": ["requests", "curl-http1"],
                "default": "requests",
                "description": "Use curl-http1 when the legacy endpoint closes Python HTTP connections.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=50, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["timeout", "rate_limit"])
    idempotency_key_fields = ["text", "voice", "model", "language_type"]
    side_effects = [
        "creates a billable DashScope speech request",
        "writes audio and redacted provider metadata files",
    ]
    user_visible_verification = [
        "Listen for pronunciation, tone, pace, and emotional fit before approving the voice",
        "Transcribe the output and compare it with the approved script",
    ]
    quality_score = 0.9
    latency_p50_seconds = 8.0

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
        rate_per_10k = 0.13 if self._region(inputs) == "singapore" else 0.114682
        return round(len(str(inputs.get("text", ""))) / 10000 * rate_per_10k, 6)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            return ToolResult(success=False, error="No DashScope API key. " + self.install_instructions)
        text = str(inputs.get("text") or "")
        if not text:
            return ToolResult(success=False, error="Qwen TTS requires non-empty text")
        if len(text) > 600:
            return ToolResult(success=False, error="Qwen3-TTS-Flash input exceeds the 600-character limit")

        import requests
        from tools.analysis.audio_probe import probe_duration

        start = time.time()
        try:
            model = str(inputs.get("model", "qwen3-tts-flash"))
            voice = str(inputs.get("voice", "Jennifer"))
            language = str(inputs.get("language_type", "English"))
            url = f"{self._base_url(inputs)}/services/aigc/multimodal-generation/generation"
            input_payload: dict[str, Any] = {
                "text": text,
                "voice": voice,
                "language_type": language,
            }
            instructions = str(inputs.get("instructions") or "").strip()
            if instructions:
                if model != "qwen3-tts-instruct-flash":
                    raise ValueError("instructions require model qwen3-tts-instruct-flash")
                input_payload["instructions"] = instructions
                input_payload["optimize_instructions"] = bool(
                    inputs.get("optimize_instructions", True)
                )
            payload = {"model": model, "input": input_payload}
            transport = str(inputs.get("transport", "requests"))
            if transport == "curl-http1":
                status_code, data = self._post_curl_http1(
                    url=url, api_key=api_key, payload=payload
                )
            else:
                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                    # A single timeout value avoids older urllib3/network stacks
                    # collapsing the (connect, read) tuple to a 10-second read
                    # window on this synchronous generation endpoint.
                    timeout=180,
                )
                status_code = response.status_code
                data = response.json()
            audio = (data.get("output") or {}).get("audio") or {}
            audio_url = audio.get("url")
            if status_code >= 400 or not audio_url:
                code = data.get("code") or "provider_error"
                message = data.get("message") or "response did not include output.audio.url"
                raise RuntimeError(f"HTTP {status_code}: {code}: {message}")
            download = requests.get(audio_url, timeout=(10, 120))
            download.raise_for_status()
            output_path = Path(inputs.get("output_path", "qwen_tts.wav"))
            metadata_path = Path(
                inputs.get("metadata_path") or output_path.with_suffix(output_path.suffix + ".json")
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(download.content)
            duration = probe_duration(output_path)
            metadata = {
                "provider": self.provider,
                "model": model,
                "voice": voice,
                "language_type": language,
                "region": self._region(inputs),
                "transport": transport,
                "request_id": data.get("request_id"),
                "audio_id": audio.get("id"),
                "expires_at": audio.get("expires_at"),
                "usage": data.get("usage"),
                "text_length": len(text),
                "instruction_control": bool(instructions),
                "audio_duration_seconds": round(duration, 2) if duration else None,
                "cost_usd_estimate": self.estimate_cost(inputs),
            }
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:
            return ToolResult(success=False, error=f"Qwen TTS failed: {exc}")

        return ToolResult(
            success=True,
            data={**metadata, "output": str(output_path), "metadata_path": str(metadata_path)},
            artifacts=[str(output_path), str(metadata_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=model,
        )

    @staticmethod
    def _post_curl_http1(
        *, url: str, api_key: str, payload: dict[str, Any]
    ) -> tuple[int, dict[str, Any]]:
        """POST through curl HTTP/1.1 without placing the API key in argv."""
        header_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", prefix="openmontage-dashscope-", suffix=".headers", delete=False
            ) as headers:
                header_path = Path(headers.name)
                os.chmod(header_path, 0o600)
                headers.write(f"Authorization: Bearer {api_key}\n")
                headers.write("Content-Type: application/json\n")
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
