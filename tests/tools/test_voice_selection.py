from tools.audio.azure_speech_tts import AzureSpeechTTS
from tools.audio.tts_selector import TTSSelector
from tools.audio.voice_catalog import rank_voice_options, voice_options

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_catalog_filters_language_without_assuming_thai():
    english = voice_options(language="en-US")
    assert english
    assert all(item.language in {"en-US", "multi"} for item in english)
    assert not any(item.voice_id == "th-TH-PremwadeeNeural" for item in english)


def test_verified_thai_voice_ranks_first_when_provider_available():
    options = voice_options(language="th-TH")
    ranked = rank_voice_options(
        options,
        language="th-TH",
        gender=None,
        tone="commercial",
        availability={"azure_speech_tts": True},
    )
    assert ranked[0].voice_id == "th-TH-PremwadeeNeural"


def test_selector_returns_three_choices_without_generating():
    result = TTSSelector().execute(
        {"text": "A short villa introduction.", "operation": "select", "language": "en-US", "tone": "luxury"}
    )
    assert result.success
    assert 1 <= len(result.data["shortlist"]) <= 3
    assert result.data["requires_owner_selection"] is True
    assert result.artifacts == []


def test_selector_rejects_unknown_selected_voice():
    result = TTSSelector().execute(
        {"text": "Hello", "operation": "generate", "selected_voice_id": "invented-voice"}
    )
    assert not result.success
    assert "Unknown selected voice" in result.error


def test_selector_does_not_substitute_unavailable_selected_voice(monkeypatch):
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("AZURE_SPEECH_REGION", raising=False)
    result = TTSSelector().execute(
        {
            "text": "Welcome to Koh Samui.",
            "operation": "generate",
            "selected_voice_id": "azure_speech:en-US-AvaMultilingualNeural",
        }
    )
    assert not result.success
    assert "no substitute was executed" in result.error


def test_azure_ssml_escapes_text_and_preserves_voice():
    ssml = AzureSpeechTTS._ssml(
        "Sea & sky < villa", "en-US-AvaMultilingualNeural", "en-US", 1.1
    )
    assert "Sea &amp; sky &lt; villa" in ssml
    assert 'name="en-US-AvaMultilingualNeural"' in ssml
    assert 'rate="+10%"' in ssml


def test_agent_cli_selects_without_generating():
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "voice_select.py"),
            "select",
            "--language",
            "en-US",
            "--tone",
            "luxury",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["success"] is True
    assert 1 <= len(payload["data"]["shortlist"]) <= 3
    assert payload["artifacts"] == []
