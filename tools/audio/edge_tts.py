"""Free Microsoft Edge speech provider with explicit voice selection."""

from __future__ import annotations

import importlib.util
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


class EdgeTTS(BaseTool):
    name = "edge_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "edge_tts"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = ["python:edge_tts"]
    install_instructions = "Install edge-tts>=7.2,<8. No API key is required."
    fallback_tools = ["azure_speech_tts", "qwen_tts", "google_tts", "piper_tts"]
    agent_skills = ["text-to-speech"]
    capabilities = ["text_to_speech", "voice_selection", "multilingual"]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": False,
        "native_audio": True,
        "timestamps": True,
    }
    best_for = [
        "zero-cost voice previews",
        "English, Thai, and multilingual short-form drafts",
        "word-boundary-aware narration that will be independently captioned",
    ]
    not_good_for = ["offline production", "voice cloning", "guaranteed service availability"]
    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string", "maxLength": 10000},
            "voice_id": {"type": "string", "default": "en-US-ChristopherNeural"},
            "speaking_rate": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
            "volume": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
            "output_path": {"type": "string"},
        },
    }
    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=50, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=0, retryable_errors=[])
    idempotency_key_fields = ["text", "voice_id", "speaking_rate", "volume"]
    side_effects = ["calls the public Edge speech service", "writes an MP3 audio file"]
    user_visible_verification = [
        "Preview voice, pronunciation, pace, and register before full synthesis",
        "Transcribe final audio before building captions",
    ]

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if importlib.util.find_spec("edge_tts") else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    @staticmethod
    def _percent(value: float) -> str:
        return f"{round((value - 1.0) * 100):+d}%"

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(success=False, error="Edge TTS unavailable. " + self.install_instructions)

        import edge_tts
        from tools.analysis.audio_probe import probe_duration

        text = str(inputs.get("text") or "").strip()
        if not text:
            return ToolResult(success=False, error="Edge TTS requires non-empty text")
        voice_id = str(inputs.get("voice_id") or "en-US-ChristopherNeural")
        speaking_rate = float(inputs.get("speaking_rate", 1.0))
        volume = float(inputs.get("volume", 1.0))
        output_path = Path(inputs.get("output_path") or "edge_tts.mp3")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        start = time.time()
        boundaries: list[dict[str, Any]] = []
        try:
            communicate = edge_tts.Communicate(
                text,
                voice_id,
                rate=self._percent(speaking_rate),
                volume=self._percent(volume),
                boundary="WordBoundary",
            )
            with output_path.open("wb") as audio:
                for chunk in communicate.stream_sync():
                    if chunk.get("type") == "audio":
                        audio.write(chunk["data"])
                    elif chunk.get("type") == "WordBoundary":
                        boundaries.append(
                            {
                                "text": chunk.get("text"),
                                "offset_100ns": chunk.get("offset"),
                                "duration_100ns": chunk.get("duration"),
                            }
                        )
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise RuntimeError("provider returned no audio")
            duration = probe_duration(output_path)
        except Exception as exc:
            output_path.unlink(missing_ok=True)
            return ToolResult(success=False, error=f"Edge TTS failed: {exc}")

        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "voice_id": voice_id,
                "speaking_rate": speaking_rate,
                "volume": volume,
                "word_boundaries": boundaries,
                "output": str(output_path),
                "audio_duration_seconds": round(duration, 2) if duration else None,
            },
            artifacts=[str(output_path)],
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 2),
            model=voice_id,
        )
