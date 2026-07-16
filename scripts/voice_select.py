#!/usr/bin/env python3
"""Strict agent CLI for cataloging, selecting, and previewing TTS voices."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audio.tts_selector import TTSSelector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("catalog", "select", "preview"))
    parser.add_argument("--language", help="BCP-47 language, for example en-US, th-TH, or zh-CN")
    parser.add_argument("--gender", choices=("female", "male", "neutral"))
    parser.add_argument("--tone", help="Delivery tone, for example warm, luxury, or documentary")
    parser.add_argument("--provider", default="auto", help="Provider name or auto")
    parser.add_argument("--selected-voice", help="Qualified provider:voice selection ID")
    parser.add_argument("--text", help="Preview text; required for preview")
    parser.add_argument("--output", type=Path, help="Preview MP3 path; required for preview")
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument("--volume", type=float, default=1.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.operation == "preview" and (not args.selected_voice or not args.text or not args.output):
        raise SystemExit("preview requires --selected-voice, --text, and --output")
    if not 0.5 <= args.rate <= 2.0 or not 0.5 <= args.volume <= 2.0:
        raise SystemExit("--rate and --volume must be between 0.5 and 2.0")

    inputs = {
        "operation": "generate" if args.operation == "preview" else args.operation,
        "text": args.text or "",
        "language": args.language,
        "gender": args.gender,
        "tone": args.tone,
        "preferred_provider": args.provider,
        "selected_voice_id": args.selected_voice,
        "speaking_rate": args.rate,
        "volume": args.volume,
        "output_path": str(args.output) if args.output else None,
    }
    inputs = {key: value for key, value in inputs.items() if value is not None}
    result = TTSSelector().execute(inputs)
    payload = {
        "success": result.success,
        "data": result.data,
        "artifacts": result.artifacts,
        "cost_usd": result.cost_usd,
        "error": result.error,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
