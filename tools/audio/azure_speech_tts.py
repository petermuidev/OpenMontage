"""Microsoft Azure Speech REST text-to-speech provider."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape, quoteattr

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


class AzureSpeechTTS(BaseTool):
    name = "azure_speech_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "azure_speech"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION. These are Azure Speech "
        "credentials, not Azure OpenAI credentials."
    )
    fallback_tools = ["qwen_tts", "google_tts", "openai_tts", "piper_tts"]
    agent_skills = ["text-to-speech"]
    capabilities = ["text_to_speech", "voice_selection", "multilingual", "ssml_support"]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": False,
        "native_audio": True,
        "timestamps": False,
        "ssml": True,
    }
    best_for = [
        "Thai narration with the locally verified Premwadee voice",
        "multilingual commercial and editorial narration",
    ]
    not_good_for = ["voice cloning", "word-level timestamps", "offline production"]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string", "maxLength": 10000},
            "voice_id": {"type": "string", "default": "th-TH-PremwadeeNeural"},
            "language": {"type": "string", "default": "th-TH"},
            "speaking_rate": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
            "output_format": {
                "type": "string",
                "enum": [
                    "audio-16khz-128kbitrate-mono-mp3",
                    "audio-24khz-160kbitrate-mono-mp3",
                ],
                "default": "audio-16khz-128kbitrate-mono-mp3",
            },
            "output_path": {"type": "string"},
        },
    }
    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=50, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=0, retryable_errors=[])
    idempotency_key_fields = ["text", "voice_id", "language", "speaking_rate", "output_format"]
    side_effects = [
        "creates a potentially billable Azure Speech request",
        "writes an audio file",
    ]
    user_visible_verification = [
        "Preview the selected voice before full synthesis",
        "Transcribe the result and compare it with the approved script",
    ]

    def get_status(self) -> ToolStatus:
        if os.environ.get("AZURE_SPEECH_KEY") and os.environ.get("AZURE_SPEECH_REGION"):
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        # Account pricing is not present in the local truth snapshot.  Do not
        # fabricate a dollar estimate; Revenue OS must still treat this API call
        # as paid because it is declared in side_effects.
        return 0.0

    @staticmethod
    def _ssml(text: str, voice_id: str, language: str, speaking_rate: float) -> str:
        percent = round((speaking_rate - 1.0) * 100)
        rate = f"{percent:+d}%"
        return (
            f"<speak version='1.0' xml:lang={quoteattr(language)}>"
            f"<voice name={quoteattr(voice_id)}>"
            f"<prosody rate={quoteattr(rate)}>{escape(text)}</prosody>"
            "</voice></speak>"
        )

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        key = os.environ.get("AZURE_SPEECH_KEY")
        region = os.environ.get("AZURE_SPEECH_REGION")
        if not key or not region:
            return ToolResult(success=False, error="Azure Speech credentials unavailable. " + self.install_instructions)

        import requests
        from tools.analysis.audio_probe import probe_duration

        text = str(inputs.get("text") or "").strip()
        if not text:
            return ToolResult(success=False, error="Azure Speech TTS requires non-empty text")
        voice_id = str(inputs.get("voice_id") or "th-TH-PremwadeeNeural")
        language = str(inputs.get("language") or "-").strip()
        if language == "-":
            language = "-".join(voice_id.split("-")[:2])
        speaking_rate = float(inputs.get("speaking_rate", 1.0))
        output_format = str(inputs.get("output_format") or "audio-16khz-128kbitrate-mono-mp3")
        output_path = Path(inputs.get("output_path") or "azure_speech_tts.mp3")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        start = time.time()
        try:
            response = requests.post(
                f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
                headers={
                    "Ocp-Apim-Subscription-Key": key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": output_format,
                    "User-Agent": "OpenMontage",
                },
                data=self._ssml(text, voice_id, language, speaking_rate).encode("utf-8"),
                timeout=(15, 180),
            )
            response.raise_for_status()
            if not response.content:
                raise RuntimeError("provider returned an empty audio payload")
            output_path.write_bytes(response.content)
            duration = probe_duration(output_path)
        except Exception as exc:
            return ToolResult(success=False, error=f"Azure Speech TTS failed: {exc}")

        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "voice_id": voice_id,
                "language": language,
                "speaking_rate": speaking_rate,
                "format": output_format,
                "output": str(output_path),
                "audio_duration_seconds": round(duration, 2) if duration else None,
                "cost_estimate_status": "unknown-account-pricing",
            },
            artifacts=[str(output_path)],
            duration_seconds=round(time.time() - start, 2),
            model=voice_id,
        )
