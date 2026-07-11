"""Focused tests for video provider preference routing."""

from __future__ import annotations

from tools.base_tool import BaseTool, ToolResult, ToolStatus, ToolTier
from tools.video.video_selector import VideoSelector


class _Provider(BaseTool):
    tier = ToolTier.GENERATE
    capability = "video_generation"
    capabilities = ["text_to_video"]
    best_for = ["generated cinematic video"]
    supports = {"text_to_video": True}

    def __init__(self, provider: str, *, available: bool = True) -> None:
        self.name = f"{provider}_video"
        self.provider = provider
        self._status = ToolStatus.AVAILABLE if available else ToolStatus.UNAVAILABLE

    def get_status(self) -> ToolStatus:
        return self._status

    def execute(self, inputs: dict[str, object]) -> ToolResult:
        return ToolResult(success=True, data={"provider": self.provider})


def _select(
    selector: VideoSelector,
    inputs: dict[str, object],
    providers: list[_Provider],
):
    context = selector._prepare_task_context(inputs)
    return selector._select_best_tool(inputs, providers, context)[0]


def test_environment_default_prefers_available_grok(monkeypatch):
    monkeypatch.setenv("VIDEO_GEN_PREFERRED_PROVIDER", "grok")
    selector = VideoSelector()

    selected = _select(
        selector,
        {"prompt": "cinematic island arrival"},
        [_Provider("other"), _Provider("grok")],
    )

    assert selected is not None
    assert selected.provider == "grok"


def test_explicit_preference_overrides_environment_default(monkeypatch):
    monkeypatch.setenv("VIDEO_GEN_PREFERRED_PROVIDER", "grok")
    selector = VideoSelector()

    selected = _select(
        selector,
        {"prompt": "cinematic island arrival", "preferred_provider": "other"},
        [_Provider("grok"), _Provider("other")],
    )

    assert selected is not None
    assert selected.provider == "other"


def test_unavailable_grok_default_falls_back_to_scored_provider(monkeypatch):
    monkeypatch.setenv("VIDEO_GEN_PREFERRED_PROVIDER", "grok")
    selector = VideoSelector()

    selected = _select(
        selector,
        {"prompt": "cinematic island arrival"},
        [_Provider("grok", available=False), _Provider("other")],
    )

    assert selected is not None
    assert selected.provider == "other"


def test_unavailable_explicit_preference_blocks_substitution(monkeypatch):
    monkeypatch.setenv("VIDEO_GEN_PREFERRED_PROVIDER", "grok")
    selector = VideoSelector()

    selected = _select(
        selector,
        {
            "prompt": "cinematic island arrival",
            "preferred_provider": "unavailable",
        },
        [_Provider("grok"), _Provider("unavailable", available=False)],
    )

    assert selected is None


def test_allowed_providers_can_exclude_environment_default(monkeypatch):
    monkeypatch.setenv("VIDEO_GEN_PREFERRED_PROVIDER", "grok")
    selector = VideoSelector()

    selected = _select(
        selector,
        {
            "prompt": "cinematic island arrival",
            "allowed_providers": ["other"],
        },
        [_Provider("grok"), _Provider("other")],
    )

    assert selected is not None
    assert selected.provider == "other"


def test_allowed_providers_excluding_explicit_preference_blocks_substitution(monkeypatch):
    monkeypatch.setenv("VIDEO_GEN_PREFERRED_PROVIDER", "grok")
    selector = VideoSelector()

    selected = _select(
        selector,
        {
            "prompt": "cinematic island arrival",
            "preferred_provider": "grok",
            "allowed_providers": ["other"],
        },
        [_Provider("grok"), _Provider("other")],
    )

    assert selected is None


def test_execute_returns_structured_blocker_for_explicit_unavailable_provider(monkeypatch):
    monkeypatch.setenv("VIDEO_GEN_PREFERRED_PROVIDER", "grok")
    selector = VideoSelector()
    providers = [_Provider("grok"), _Provider("unavailable", available=False)]
    monkeypatch.setattr(selector, "_providers", lambda: providers)

    result = selector.execute(
        {
            "prompt": "cinematic island arrival",
            "preferred_provider": "unavailable",
        }
    )

    assert result.success is False
    assert result.data["requested_provider"] == "unavailable"
    assert result.data["available_alternatives"] == ["grok"]
    assert result.data["requires_user_approval"] is True
    assert "No substitute was executed" in result.error


def test_blocker_alternatives_respect_allowed_providers(monkeypatch):
    selector = VideoSelector()
    providers = [_Provider("grok"), _Provider("other")]
    monkeypatch.setattr(selector, "_providers", lambda: providers)

    result = selector.execute(
        {
            "prompt": "cinematic island arrival",
            "preferred_provider": "grok",
            "allowed_providers": ["other"],
        }
    )

    assert result.success is False
    assert result.data["available_alternatives"] == ["other"]
    assert result.data["requires_user_approval"] is True
