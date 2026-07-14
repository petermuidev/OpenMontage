#!/usr/bin/env python3
"""Recompose and verify the owner-accepted Samui multi-shot baseline.

This command is deliberately offline. It cannot invoke image, video, or TTS
providers and therefore cannot create spend or replace approved source media.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import PIL
from PIL import Image, ImageDraw, ImageFont


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = SKILL_ROOT / "references" / "samui_multishot_baseline.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command[:4])}\n"
            f"{result.stderr[-2000:]}"
        )
    return result


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported baseline manifest schema")
    if not data.get("shots") or len(data["shots"]) < 4:
        raise ValueError("A comparable multi-shot baseline requires at least four shots")
    if data.get("paid_regeneration", {}).get("enabled_by_this_manifest") is not False:
        raise ValueError("Reproduction manifest must explicitly disable paid regeneration")
    return data


def resolve(project_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else project_root / path


def verified_inputs(manifest: dict[str, Any], project_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    resolved: dict[str, Any] = {"shots": []}
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            errors.append(f"Missing required executable: {tool}")
    toolchain = manifest.get("toolchain", {})
    if shutil.which("ffmpeg"):
        ffmpeg_line = run(["ffmpeg", "-version"]).stdout.splitlines()[0]
        if f"ffmpeg version {toolchain.get('ffmpeg')}" not in ffmpeg_line:
            errors.append(
                f"FFmpeg version mismatch: expected {toolchain.get('ffmpeg')}, got {ffmpeg_line}"
            )
    python_version = platform.python_version()
    if python_version != toolchain.get("python"):
        errors.append(
            f"Python version mismatch: expected {toolchain.get('python')}, got {python_version}"
        )
    if PIL.__version__ != toolchain.get("pillow"):
        errors.append(
            f"Pillow version mismatch: expected {toolchain.get('pillow')}, got {PIL.__version__}"
        )
    font = resolve(project_root, manifest["render"]["font_path"])
    if not font.is_file():
        errors.append(f"Missing font: {font}")
    resolved["font"] = font

    for section in ("narration", "music"):
        entry = manifest[section]
        path = resolve(project_root, entry["path"])
        if not path.is_file():
            errors.append(f"Missing {section}: {path}")
        elif sha256(path) != entry["sha256"]:
            errors.append(f"{section} hash mismatch: {path}")
        resolved[section] = path

    for index, shot in enumerate(manifest["shots"], start=1):
        path = resolve(project_root, shot["source"])
        if not path.is_file():
            errors.append(f"Missing shot {index}: {path}")
        elif sha256(path) != shot["sha256"]:
            errors.append(f"Shot {index} hash mismatch: {path}")
        resolved["shots"].append(path)

    master = resolve(project_root, manifest["accepted_master"]["path"])
    if not master.is_file():
        errors.append(f"Missing accepted master: {master}")
    elif sha256(master) != manifest["accepted_master"]["sha256"]:
        errors.append(f"Accepted master hash mismatch: {master}")
    resolved["master"] = master

    if errors:
        raise RuntimeError("Preflight failed:\n- " + "\n- ".join(errors))
    return resolved


def make_overlays(
    manifest: dict[str, Any], font_path: Path, output_dir: Path
) -> list[Path]:
    render = manifest["render"]
    width, height = int(render["width"]), int(render["height"])
    output_dir.mkdir(parents=True, exist_ok=True)
    brand_font = ImageFont.truetype(str(font_path), int(render["brand_font_size"]))
    overlays: list[Path] = []
    for index, shot in enumerate(manifest["shots"], start=1):
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        brand = str(render["brand"])
        box = draw.textbbox((0, 0), brand, font=brand_font)
        text_width, text_height = box[2] - box[0], box[3] - box[1]
        x = (width - text_width) // 2
        y = int(render["brand_y"])
        draw.rounded_rectangle(
            (x - 14, y - 10, x + text_width + 14, y + text_height + 12),
            radius=12,
            fill=(0, 0, 0, 56),
        )
        draw.text((x, y), brand, font=brand_font, fill=(255, 255, 255, 210))

        caption = str(shot["caption"])
        caption_font = ImageFont.truetype(str(font_path), int(shot["caption_font_size"]))
        box = draw.textbbox((0, 0), caption, font=caption_font)
        text_width, text_height = box[2] - box[0], box[3] - box[1]
        x = (width - text_width) // 2
        y = int(render["caption_y"])
        draw.rounded_rectangle(
            (x - 25, y - 18, x + text_width + 25, y + text_height + 22),
            radius=18,
            fill=(0, 0, 0, 102),
        )
        draw.text(
            (x, y), caption, font=caption_font, fill=tuple(shot["caption_color"])
        )
        path = output_dir / f"overlay-{index:02d}.png"
        image.save(path, optimize=True)
        overlays.append(path)
    return overlays


def compose(
    manifest: dict[str, Any], resolved: dict[str, Any], output: Path, force: bool
) -> dict[str, Any]:
    if output.exists() and not force:
        raise FileExistsError(f"Output exists; pass --force to replace it: {output}")
    work_dir = output.parent / f".{output.stem}-work"
    overlay_dir = work_dir / "overlays"
    work_dir.mkdir(parents=True, exist_ok=True)
    overlays = make_overlays(manifest, resolved["font"], overlay_dir)
    intermediate = work_dir / "assembled.mp4"
    render = manifest["render"]
    duration = float(render["duration_seconds"])

    command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    for shot in resolved["shots"]:
        command += ["-i", str(shot)]
    command += ["-i", str(resolved["narration"]), "-i", str(resolved["music"])]
    for overlay in overlays:
        command += ["-loop", "1", "-i", str(overlay)]

    video_filters: list[str] = []
    for index, shot in enumerate(manifest["shots"]):
        video_filters.append(
            f"[{index}:v]trim=start=0:end={shot['source_trim_seconds']},"
            f"setpts={shot['speed_factor']}*(PTS-STARTPTS),"
            f"scale={render['width']}:{render['height']}:flags=lanczos,"
            f"fps={render['fps']},format=yuv420p[v{index}]"
        )
    joined = "".join(f"[v{i}]" for i in range(len(manifest["shots"])))
    video_filters.append(
        f"{joined}concat=n={len(manifest['shots'])}:v=1:a=0,"
        f"trim=duration={duration}[base]"
    )
    first_overlay_input = len(manifest["shots"]) + 2
    previous = "base"
    for index, shot in enumerate(manifest["shots"]):
        output_label = "v" if index == len(manifest["shots"]) - 1 else f"c{index + 1}"
        start, end = shot["caption_enable"]
        video_filters.append(
            f"[{previous}][{first_overlay_input + index}:v]overlay=0:0:"
            f"enable='between(t,{start},{end})'[{output_label}]"
        )
        previous = output_label

    voice_input = len(manifest["shots"])
    music_input = voice_input + 1
    narration = manifest["narration"]
    music = manifest["music"]
    audio_filters = [
        f"[{voice_input}:a]aresample=48000,"
        f"loudnorm=I={narration['target_lufs']}:TP={narration['true_peak_db']}:"
        f"LRA={narration['lra']},apad=pad_dur={duration},"
        f"atrim=duration={duration}[vo]",
        f"[{music_input}:a]atrim=start=0:end={duration},asetpts=PTS-STARTPTS,"
        f"aresample=48000,volume={music['gain']},"
        f"afade=t=in:st=0:d={music['fade_in_seconds']},"
        f"afade=t=out:st={music['fade_out_start']}:d={music['fade_out_seconds']}[m]",
        "[vo][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        "alimiter=limit=0.95[a]",
    ]
    filter_complex = ";".join(video_filters + audio_filters)
    command += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-preset",
        str(render["video_preset"]),
        "-crf",
        str(render["video_crf"]),
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(render["fps"]),
        "-c:a",
        "aac",
        "-b:a",
        str(render["audio_bitrate"]),
        "-movflags",
        "+faststart",
        "-t",
        str(duration),
        str(intermediate),
        "-y",
    ]
    run(command)

    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(intermediate),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            str(render["audio_bitrate"]),
            "-ar",
            str(render["audio_sample_rate"]),
            "-movflags",
            "+faststart",
            str(output),
            "-y",
        ]
    )
    return qa(manifest, output)


def qa(manifest: dict[str, Any], output: Path) -> dict[str, Any]:
    if not output.is_file():
        raise FileNotFoundError(f"QA output not found: {output}")
    probe = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=index,codec_name,width,height,pix_fmt,r_frame_rate,sample_rate,channels:format=duration,size",
                "-of",
                "json",
                str(output),
            ]
        ).stdout
    )
    streams = probe.get("streams", [])
    video = next((item for item in streams if item.get("width")), {})
    audio = next((item for item in streams if item.get("sample_rate")), {})
    render = manifest["render"]
    errors: list[str] = []
    checks = {
        "width": (video.get("width"), int(render["width"])),
        "height": (video.get("height"), int(render["height"])),
        "video_codec": (video.get("codec_name"), "h264"),
        "pixel_format": (video.get("pix_fmt"), "yuv420p"),
        "fps": (video.get("r_frame_rate"), f"{render['fps']}/1"),
        "audio_codec": (audio.get("codec_name"), "aac"),
        "audio_sample_rate": (
            int(audio.get("sample_rate", 0)),
            int(render["audio_sample_rate"]),
        ),
    }
    for name, (actual, expected) in checks.items():
        if actual != expected:
            errors.append(f"{name}: expected {expected}, got {actual}")
    duration = float(probe.get("format", {}).get("duration", 0))
    accepted_duration = 10.166667
    if abs(duration - accepted_duration) > 0.02:
        errors.append(f"duration: expected ~{accepted_duration}, got {duration}")
    actual_hash = sha256(output)
    expected_hash = manifest["accepted_master"]["sha256"]
    if actual_hash != expected_hash:
        errors.append(f"sha256: expected {expected_hash}, got {actual_hash}")
    report = {
        "status": "PASS" if not errors else "FAIL",
        "output": str(output),
        "sha256": actual_hash,
        "exact_baseline_match": actual_hash == expected_hash,
        "duration_seconds": duration,
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": video.get("r_frame_rate"),
        "audio_sample_rate": audio.get("sample_rate"),
        "errors": errors,
    }
    if errors:
        raise RuntimeError(json.dumps(report, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Validate tools, paths, and hashes only")
    action.add_argument("--compose", action="store_true", help="Recompose locally without provider calls")
    action.add_argument("--qa-only", action="store_true", help="Verify an existing output")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest.resolve())
    project_root = (args.project_root or Path(manifest["project_root"])).expanduser().resolve()
    resolved = verified_inputs(manifest, project_root)
    if args.qa_only:
        output = (args.output or resolved["master"]).expanduser().resolve()
        report = qa(manifest, output)
    elif args.compose:
        output = (
            args.output
            or project_root / ".work" / "reproduction" / "samui-motivation-multishot-final.mp4"
        ).expanduser().resolve()
        report = compose(manifest, resolved, output, args.force)
    else:
        report = {
            "status": "PASS",
            "mode": "check",
            "project_root": str(project_root),
            "shots": len(resolved["shots"]),
            "accepted_master": str(resolved["master"]),
            "toolchain": manifest["toolchain"],
            "paid_provider_calls": False,
        }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
