#!/usr/bin/env python3
"""Validate the durable media recipe catalog without rendering or provider calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/recipes/catalog.json"
ALLOWED_STATUS = {
    "accepted-baseline",
    "accepted-pattern",
    "proven-candidate",
    "reference-only",
    "superseded",
}
ALLOWED_LANES = {"commercial-showcase", "source-transformation", "engagement", "editorial"}
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
VIDEO_PATH_RE = re.compile(r"\.(mp4|mov|webm)$", re.IGNORECASE)
REQUIRED = {
    "schema_version",
    "recipe_id",
    "title",
    "status",
    "lane",
    "best_for",
    "source_contract",
    "creative_contract",
    "qa_contract",
    "canonical_artifacts",
    "proof",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_recipe(recipe: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED - recipe.keys())
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
        return errors
    rid = recipe["recipe_id"]
    if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]+", rid):
        errors.append(f"{path}: invalid recipe_id")
    if recipe["schema_version"] != "1.0":
        errors.append(f"{path}: schema_version must be 1.0")
    if recipe["status"] not in ALLOWED_STATUS:
        errors.append(f"{path}: unknown status {recipe['status']!r}")
    if recipe["lane"] not in ALLOWED_LANES:
        errors.append(f"{path}: unknown lane {recipe['lane']!r}")
    for field in ("best_for", "source_contract", "creative_contract", "qa_contract"):
        value = recipe[field]
        if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
            errors.append(f"{path}: {field} must be a non-empty string list")
    artifacts = recipe["canonical_artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        errors.append(f"{path}: canonical_artifacts must be non-empty")
    else:
        if not any(isinstance(artifact, dict) and artifact.get("tracked") is True for artifact in artifacts):
            errors.append(f"{path}: canonical_artifacts requires a tracked portable contract")
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict) or artifact.get("repo") not in {"openmontage", "face"}:
                errors.append(f"{path}: canonical_artifacts[{index}] has invalid repo")
            if not isinstance(artifact, dict) or not artifact.get("path") or not artifact.get("role"):
                errors.append(f"{path}: canonical_artifacts[{index}] lacks path or role")
    proof = recipe["proof"]
    if not isinstance(proof, dict) or not proof.get("disposition") or not proof.get("qa"):
        errors.append(f"{path}: proof requires disposition and qa")
    else:
        output = proof.get("output_path")
        if not isinstance(output, str) or not VIDEO_PATH_RE.search(output):
            errors.append(f"{path}: proof.output_path must name the successful video output")
        if proof.get("output_repo") not in {"openmontage", "face"}:
            errors.append(f"{path}: proof.output_repo must be openmontage or face")
        digest = proof.get("output_sha256")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            errors.append(f"{path}: proof.output_sha256 is not SHA-256")
    if recipe["status"] == "superseded" and not recipe.get("superseded_by"):
        errors.append(f"{path}: superseded recipe requires superseded_by")
    return errors


def local_path(repo: str, relative: str, roots: dict[str, str]) -> Path:
    return Path(roots[repo]).expanduser() / relative


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-local-proofs", action="store_true", help="verify proof hashes when local outputs exist")
    args = parser.parse_args()

    try:
        catalog = load_json(CATALOG)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    roots = catalog.get("repository_roots", {})
    entries = catalog.get("recipes")
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    if not isinstance(entries, list) or not entries:
        errors.append("catalog recipes must be a non-empty list")
        entries = []

    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("recipe_id") or not entry.get("record"):
            errors.append("catalog entry requires recipe_id and record")
            continue
        rid = entry["recipe_id"]
        if rid in seen:
            errors.append(f"duplicate recipe_id: {rid}")
        seen.add(rid)
        record_path = CATALOG.parent / entry["record"]
        try:
            recipe = load_json(record_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if recipe.get("recipe_id") != rid:
            errors.append(f"{record_path}: recipe_id does not match catalog entry {rid}")
        errors.extend(validate_recipe(recipe, record_path))
        records.append(recipe)

    ids = {recipe.get("recipe_id") for recipe in records}
    for recipe in records:
        successor = recipe.get("superseded_by")
        if successor and successor not in ids:
            errors.append(f"{recipe['recipe_id']}: unknown superseded_by {successor}")
        for artifact in recipe.get("canonical_artifacts", []):
            repo = artifact.get("repo")
            if repo not in roots:
                errors.append(f"{recipe['recipe_id']}: no repository root configured for {repo}")
                continue
            path = local_path(repo, artifact["path"], roots)
            if not path.exists():
                warnings.append(f"{recipe['recipe_id']}: local artifact absent: {path}")
        if args.check_local_proofs:
            proof = recipe.get("proof", {})
            expected = proof.get("output_sha256")
            output = proof.get("output_path")
            if expected and output:
                output_repo = proof.get("output_repo")
                path = local_path(output_repo, output, roots)
                if path.exists():
                    actual = sha256(path)
                    if actual != expected:
                        errors.append(f"{recipe['recipe_id']}: proof hash mismatch: {actual} != {expected}")
                else:
                    warnings.append(f"{recipe['recipe_id']}: proof output absent; hash skipped: {path}")

    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    counts = {status: sum(recipe.get("status") == status for recipe in records) for status in ALLOWED_STATUS}
    print(f"PASS: {len(records)} media recipes validated: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
