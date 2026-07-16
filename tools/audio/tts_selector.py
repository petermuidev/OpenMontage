"""Capability-level text-to-speech selector that chooses among provider tools.

Provider discovery is automatic — any BaseTool with capability="tts"
is picked up from the registry.  Adding a new TTS provider requires only creating
the tool file in tools/audio/; no changes to this selector are needed.
"""

from __future__ import annotations

from typing import Any

from tools.base_tool import BaseTool, ToolResult, ToolRuntime, ToolStability, ToolTier, ToolStatus


class TTSSelector(BaseTool):
    name = "tts_selector"
    version = "0.2.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "selector"
    stability = ToolStability.BETA
    runtime = ToolRuntime.HYBRID
    agent_skills = ["text-to-speech", "elevenlabs", "openai-docs"]

    capabilities = [
        "text_to_speech",
        "provider_selection",
    ]
    supports = {
        "user_preference_routing": True,
        "offline_fallback": True,
        "multilingual": True,
    }
    best_for = [
        "preflight tool selection",
        "user-facing recommendation flows",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string"},
            "voice_id": {
                "type": "string",
                "description": "Provider-specific voice ID. Passed through to the selected TTS provider.",
            },
            "model_id": {
                "type": "string",
                "description": "TTS model to use (e.g. eleven_multilingual_v2). Passed through to provider.",
            },
            "stability": {
                "type": "number", "minimum": 0, "maximum": 1,
                "description": "Voice stability (ElevenLabs). Lower = more expressive.",
            },
            "similarity_boost": {
                "type": "number", "minimum": 0, "maximum": 1,
                "description": "Voice similarity boost (ElevenLabs).",
            },
            "style": {
                "type": "number", "minimum": 0, "maximum": 1,
                "description": "Style exaggeration (ElevenLabs). Higher = more expressive.",
            },
            "output_format": {
                "type": "string",
                "description": "Audio output format (e.g. mp3_44100_128). Passed through to provider.",
            },
            "preferred_provider": {
                "type": "string",
                "description": "Provider name or 'auto'. Valid values are discovered at runtime from the registry.",
                "default": "auto",
            },
            "allowed_providers": {
                "type": "array",
                "items": {"type": "string"},
            },
            "operation": {
                "type": "string",
                "enum": ["generate", "rank", "catalog", "select"],
                "default": "generate",
                "description": "Catalog and select never generate audio. Generate requires an explicit selected_voice_id when supplied by the voice chooser.",
            },
            "language": {"type": "string", "description": "BCP-47 narration language, e.g. en-US, th-TH, zh-CN."},
            "gender": {"type": "string", "enum": ["female", "male", "neutral"]},
            "tone": {"type": "string", "description": "Desired delivery tone such as warm, luxury, documentary, or commercial."},
            "selected_voice_id": {"type": "string", "description": "Voice ID selected after preview/owner choice."},
            "speaking_rate": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
            "volume": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
            "output_path": {"type": "string"},
        },
    }

    def _providers(self) -> list[BaseTool]:
        """Auto-discover TTS providers from the registry."""
        from tools.tool_registry import registry
        registry.ensure_discovered()
        return [t for t in registry.get_by_capability("tts")
                if t.name != self.name]

    @property
    def fallback_tools(self) -> list[str]:
        """Dynamically built from discovered providers."""
        return [t.name for t in self._providers()]

    @property
    def provider_matrix(self) -> dict[str, dict[str, str]]:
        """Built at runtime from each provider's best_for field."""
        matrix = {}
        for tool in self._providers():
            strength = ", ".join(tool.best_for) if tool.best_for else tool.name
            matrix[tool.provider] = {"tool": tool.name, "strength": strength}
        return matrix

    def get_status(self) -> ToolStatus:
        if any(tool.get_status() == ToolStatus.AVAILABLE for tool in self._providers()):
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        candidates = self._providers()
        if not candidates:
            return 0.0
        tool, _ = self._select_best_tool(inputs, candidates, self._prepare_task_context(inputs))
        return tool.estimate_cost(inputs) if tool else 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        from lib.scoring import rank_providers
        from tools.audio.voice_catalog import rank_voice_options, voice_options

        task_context = self._prepare_task_context(inputs)
        candidates = self._providers()

        availability = {
            tool.name: tool.get_status() == ToolStatus.AVAILABLE for tool in candidates
        }
        operation = inputs.get("operation", "generate")
        if operation in {"catalog", "select"}:
            provider_filter = inputs.get("preferred_provider")
            if provider_filter == "auto":
                provider_filter = None
            options = voice_options(
                language=inputs.get("language"),
                gender=inputs.get("gender"),
                provider=provider_filter,
            )
            ranked = rank_voice_options(
                options,
                language=inputs.get("language"),
                gender=inputs.get("gender"),
                tone=inputs.get("tone"),
                availability=availability,
            )
            serialized = [
                option.to_dict(available=availability.get(option.tool_name, False))
                for option in ranked
            ]
            if operation == "catalog":
                return ToolResult(success=True, data={"voices": serialized, "count": len(serialized)})

            selected_id = str(inputs.get("selected_voice_id") or "")
            selected = next((item for item in serialized if item["selection_id"] == selected_id), None)
            return ToolResult(
                success=True,
                data={
                    "shortlist": serialized[:3],
                    "selected": selected,
                    "requires_owner_selection": selected is None,
                    "next_action": "preview one shortlisted voice, then submit selected_voice_id before generation" if selected is None else "generate a bounded preview with the selected voice",
                },
            )

        # Rank mode — return scored provider rankings without generating
        if operation == "rank":
            rankings = rank_providers(candidates, task_context)
            return ToolResult(
                success=True,
                data={
                    "rankings": self._serialize_rankings(candidates, rankings),
                    "explanation": "\n".join(r.explain() for r in rankings[:5]),
                    "normalized_task_context": task_context,
                },
            )

        # Normal generation — honor the selected catalog voice and its provider.
        selected_voice_id = str(inputs.get("selected_voice_id") or "")
        if selected_voice_id:
            matches = [option for option in voice_options() if option.selection_id == selected_voice_id]
            if not matches:
                return ToolResult(success=False, error=f"Unknown selected voice: {selected_voice_id}")
            selected = matches[0]
            preferred = inputs.get("preferred_provider", "auto")
            if preferred not in {"auto", selected.provider}:
                return ToolResult(
                    success=False,
                    error=f"Selected voice {selected_voice_id} belongs to {selected.provider}, not {preferred}",
                )
            inputs = dict(inputs)
            inputs["preferred_provider"] = selected.provider
            inputs[selected.input_field] = selected.voice_id
            if selected.input_field == "voice_id":
                inputs.setdefault("voice", selected.voice_id)
            if selected.language != "multi":
                inputs.setdefault("language", selected.language)
                inputs.setdefault("language_code", selected.language)

            selected_tool = next((tool for tool in candidates if tool.name == selected.tool_name), None)
            if selected_tool is None or selected_tool.get_status() != ToolStatus.AVAILABLE:
                return ToolResult(
                    success=False,
                    error=(
                        f"Selected voice {selected_voice_id} is unavailable because "
                        f"provider {selected.provider} is not configured; no substitute was executed"
                    ),
                )

        # Normal generation — use scored selection
        tool, score = self._select_best_tool(inputs, candidates, task_context)
        if tool is None:
            return ToolResult(success=False, error="No TTS provider available.")

        result = tool.execute(inputs)
        if result.success:
            result.data.setdefault("selected_tool", tool.name)
            result.data["selected_provider"] = tool.provider
            result.data["selection_reason"] = score.explain() if score else f"Selected {tool.provider} ({tool.name})"
            if score:
                result.data["provider_score"] = score.to_dict()
            result.data.update(self._tool_context_payload(tool))
            result.data["alternatives_considered"] = [
                t.name for t in candidates
                if t.name != tool.name and t.get_status().value == "available"
            ]
        return result

    def _select_best_tool(
        self,
        inputs: dict[str, Any],
        candidates: list[BaseTool],
        task_context: dict[str, Any],
    ) -> tuple[BaseTool | None, object]:
        """Select the best TTS provider using scored ranking."""
        from lib.scoring import rank_providers

        preferred = inputs.get("preferred_provider", "auto")
        allowed = set(inputs.get("allowed_providers") or [])
        if allowed:
            candidates = [tool for tool in candidates if tool.provider in allowed]

        rankings = rank_providers(candidates, task_context)

        tool_by_provider: dict[str, BaseTool] = {}
        for tool in candidates:
            if tool.provider not in tool_by_provider and tool.get_status() == ToolStatus.AVAILABLE:
                tool_by_provider[tool.provider] = tool

        if preferred != "auto":
            for score_item in rankings:
                if score_item.provider == preferred and score_item.provider in tool_by_provider:
                    return tool_by_provider[score_item.provider], score_item
            return None, None

        for score_item in rankings:
            if score_item.provider in tool_by_provider:
                return tool_by_provider[score_item.provider], score_item

        return None, None

    def _prepare_task_context(self, inputs: dict[str, Any]) -> dict[str, Any]:
        from lib.scoring import normalize_task_context

        return normalize_task_context(
            inputs.get("task_context", {}),
            prompt=inputs.get("text", ""),
            capability=self.capability,
            operation=inputs.get("operation", "generate"),
        )

    @staticmethod
    def _tool_context_payload(tool: BaseTool) -> dict[str, Any]:
        info = tool.get_info()
        return {
            "selected_tool_agent_skills": info.get("agent_skills", []),
            "required_agent_skills": info.get("agent_skills", []),
            "selected_tool_usage_location": info.get("usage_location"),
            "selected_tool_best_for": info.get("best_for", []),
        }

    def _serialize_rankings(self, candidates: list[BaseTool], rankings: list[object]) -> list[dict[str, Any]]:
        tool_by_name = {tool.name: tool for tool in candidates}
        serialized: list[dict[str, Any]] = []
        for score in rankings:
            item = score.to_dict()
            tool = tool_by_name.get(score.tool_name)
            if tool:
                info = tool.get_info()
                item["agent_skills"] = info.get("agent_skills", [])
                item["usage_location"] = info.get("usage_location")
                item["best_for"] = info.get("best_for", [])
                item["status"] = str(tool.get_status())
            serialized.append(item)
        return serialized
