"""Small, provider-neutral voice catalog used before TTS generation.

The catalog is intentionally curated rather than pretending every provider
voice has been tested.  ``verified`` means the voice has a recorded local
probe; ``candidate`` means the provider documents the voice but it still needs
an owner preview before production.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class VoiceOption:
    voice_id: str
    provider: str
    tool_name: str
    input_field: str
    language: str
    label: str
    gender: str
    tones: tuple[str, ...]
    evidence: str

    @property
    def selection_id(self) -> str:
        return f"{self.provider}:{self.voice_id}"

    def to_dict(self, *, available: bool) -> dict:
        data = asdict(self)
        data["tones"] = list(self.tones)
        data["selection_id"] = self.selection_id
        data["available"] = available
        return data


VOICE_OPTIONS: tuple[VoiceOption, ...] = (
    VoiceOption(
        "th-TH-PremwadeeNeural", "edge_tts", "edge_tts", "voice_id",
        "th-TH", "Premwadee — Thai female (free Edge)", "female",
        ("warm", "commercial", "editorial"), "candidate",
    ),
    VoiceOption(
        "th-TH-NiwatNeural", "edge_tts", "edge_tts", "voice_id",
        "th-TH", "Niwat — Thai male (free Edge)", "male",
        ("calm", "informative", "editorial"), "candidate",
    ),
    VoiceOption(
        "en-US-ChristopherNeural", "edge_tts", "edge_tts", "voice_id",
        "en-US", "Christopher — English male (free Edge)", "male",
        ("calm", "documentary", "commercial"), "verified",
    ),
    VoiceOption(
        "en-US-AvaMultilingualNeural", "edge_tts", "edge_tts", "voice_id",
        "en-US", "Ava — English multilingual female (free Edge)", "female",
        ("warm", "luxury", "commercial"), "candidate",
    ),
    VoiceOption(
        "th-TH-PremwadeeNeural", "azure_speech", "azure_speech_tts", "voice_id",
        "th-TH", "Premwadee — Thai female", "female",
        ("warm", "commercial", "editorial"), "verified",
    ),
    VoiceOption(
        "th-TH-NiwatNeural", "azure_speech", "azure_speech_tts", "voice_id",
        "th-TH", "Niwat — Thai male", "male",
        ("calm", "informative", "editorial"), "candidate",
    ),
    VoiceOption(
        "en-US-AvaMultilingualNeural", "azure_speech", "azure_speech_tts", "voice_id",
        "en-US", "Ava — English multilingual female", "female",
        ("warm", "luxury", "commercial"), "candidate",
    ),
    VoiceOption(
        "en-US-AndrewMultilingualNeural", "azure_speech", "azure_speech_tts", "voice_id",
        "en-US", "Andrew — English multilingual male", "male",
        ("calm", "luxury", "documentary"), "candidate",
    ),
    VoiceOption(
        "zh-CN-XiaoxiaoMultilingualNeural", "azure_speech", "azure_speech_tts", "voice_id",
        "zh-CN", "Xiaoxiao — Mandarin multilingual female", "female",
        ("warm", "commercial", "story"), "candidate",
    ),
    VoiceOption(
        "Jennifer", "dashscope_qwen", "qwen_tts", "voice",
        "en-US", "Jennifer — Qwen English female", "female",
        ("editorial", "commercial", "expressive"), "verified",
    ),
    VoiceOption(
        "en-US-Chirp3-HD-Aoede", "google_tts", "google_tts", "voice",
        "en-US", "Aoede — English female", "female",
        ("warm", "story", "commercial"), "candidate",
    ),
    VoiceOption(
        "en-US-Chirp3-HD-Orus", "google_tts", "google_tts", "voice",
        "en-US", "Orus — English male", "male",
        ("rich", "cinematic", "documentary"), "candidate",
    ),
    VoiceOption(
        "alloy", "openai", "openai_tts", "voice",
        "multi", "Alloy — multilingual neutral", "neutral",
        ("neutral", "editorial", "prototype"), "candidate",
    ),
    VoiceOption(
        "21m00Tcm4TlvDq8ikWAM", "elevenlabs", "elevenlabs_tts", "voice_id",
        "multi", "Rachel — multilingual female", "female",
        ("natural", "story", "premium"), "candidate",
    ),
    VoiceOption(
        "en_US-lessac-medium", "piper", "piper_tts", "model",
        "en-US", "Lessac — local English female", "female",
        ("offline", "draft", "neutral"), "candidate",
    ),
)


def voice_options(
    *,
    language: str | None = None,
    gender: str | None = None,
    provider: str | None = None,
) -> list[VoiceOption]:
    """Return catalog options matching explicit user constraints."""
    language = (language or "").lower()
    gender = (gender or "").lower()
    provider = (provider or "").lower()
    result: list[VoiceOption] = []
    for option in VOICE_OPTIONS:
        if language and option.language.lower() not in {language, "multi"}:
            continue
        if gender and option.gender.lower() != gender:
            continue
        if provider and option.provider.lower() != provider:
            continue
        result.append(option)
    return result


def rank_voice_options(
    options: list[VoiceOption],
    *,
    language: str | None,
    gender: str | None,
    tone: str | None,
    availability: dict[str, bool],
) -> list[VoiceOption]:
    """Rank without hiding unavailable choices or inventing voice quality."""
    language = (language or "").lower()
    gender = (gender or "").lower()
    tone = (tone or "").lower()

    def score(option: VoiceOption) -> tuple[int, str, str]:
        value = 0
        if availability.get(option.tool_name, False):
            value += 8
        if language and option.language.lower() == language:
            value += 6
        elif language and option.language == "multi":
            value += 2
        if gender and option.gender.lower() == gender:
            value += 2
        if tone and tone in {item.lower() for item in option.tones}:
            value += 3
        if option.evidence == "verified":
            value += 2
        return (-value, option.provider, option.voice_id)

    return sorted(options, key=score)
