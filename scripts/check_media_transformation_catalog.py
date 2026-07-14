#!/usr/bin/env python3
"""Validate Transformation Catalogue V2 without rendering or provider calls."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "docs/recipes/v2"
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def load(name: str) -> dict[str, Any]:
    path = V2 / name
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def unique_ids(rows: Any, field: str, label: str, errors: list[str]) -> set[str]:
    if not isinstance(rows, list) or not rows:
        errors.append(f"{label}: expected non-empty list")
        return set()
    values: list[str] = []
    for index, row in enumerate(rows):
        value = row.get(field) if isinstance(row, dict) else None
        if not isinstance(value, str) or not value:
            errors.append(f"{label}[{index}]: missing {field}")
        else:
            values.append(value)
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        errors.append(f"{label}: duplicate IDs: {', '.join(duplicates)}")
    return set(values)


def validate_proposal(proposal: dict[str, Any], kernel_ids: set[str], treatment_ids: set[str], profile_ids: set[str], compatible: set[tuple[str, str]], errors: list[str]) -> None:
    required = {"schema_version", "proposal_id", "source", "inventory", "reference_signal", "candidates", "selected_route", "decision_log"}
    missing = sorted(required - proposal.keys())
    if missing:
        errors.append(f"example proposal missing: {', '.join(missing)}")
        return
    source = proposal.get("source")
    if isinstance(source, dict) and source.get("role") in {"authorized-source", "reference-with-separate-sources"}:
        if not isinstance(source.get("sha256"), str) or not SHA256.fullmatch(source["sha256"]):
            errors.append("authorized example source must have a valid SHA-256")
    candidates = proposal.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 3:
        errors.append("example proposal must contain exactly three candidates")
        return
    ranks = {candidate.get("rank") for candidate in candidates if isinstance(candidate, dict)}
    if ranks != {1, 2, 3}:
        errors.append("example proposal ranks must be 1, 2, and 3")
    for candidate in candidates:
        kernel = candidate.get("kernel_id")
        treatment = candidate.get("treatment_id")
        profile = candidate.get("profile_id")
        if kernel not in kernel_ids:
            errors.append(f"example proposal unknown kernel: {kernel}")
        if treatment not in treatment_ids:
            errors.append(f"example proposal unknown treatment: {treatment}")
        if profile not in profile_ids:
            errors.append(f"example proposal unknown profile: {profile}")
        if (kernel, treatment) not in compatible:
            errors.append(f"example proposal incompatible route: {kernel} + {treatment}")


def main() -> int:
    errors: list[str] = []
    try:
        kernels = load("kernels.json")
        treatments = load("treatments.json")
        profiles = load("delivery_profiles.json")
        compatibility = load("compatibility.json")
        proposal = load("examples/transformation_proposal.example.json")
        json.loads((V2 / "transformation-proposal.schema.json").read_text(encoding="utf-8"))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    kernel_rows = kernels.get("kernels")
    treatment_rows = treatments.get("treatments")
    profile_rows = profiles.get("profiles")
    kernel_ids = unique_ids(kernel_rows, "kernel_id", "kernels", errors)
    treatment_ids = unique_ids(treatment_rows, "treatment_id", "treatments", errors)
    profile_ids = unique_ids(profile_rows, "profile_id", "profiles", errors)

    compatible: set[tuple[str, str]] = set()
    rules = compatibility.get("rules")
    if compatibility.get("default") != "rejected":
        errors.append("compatibility default must be rejected")
    if not isinstance(rules, list) or not rules:
        errors.append("compatibility rules must be non-empty")
        rules = []
    for index, rule in enumerate(rules):
        kernel = rule.get("kernel_id") if isinstance(rule, dict) else None
        listed = rule.get("treatments") if isinstance(rule, dict) else None
        status = rule.get("status") if isinstance(rule, dict) else None
        gates = rule.get("gates") if isinstance(rule, dict) else None
        if kernel not in kernel_ids:
            errors.append(f"compatibility[{index}]: unknown kernel {kernel}")
        if status not in {"allowed", "conditional"}:
            errors.append(f"compatibility[{index}]: invalid status {status}")
        if not isinstance(gates, list) or not gates:
            errors.append(f"compatibility[{index}]: gates must be non-empty")
        if not isinstance(listed, list) or not listed:
            errors.append(f"compatibility[{index}]: treatments must be non-empty")
            continue
        for treatment in listed:
            if treatment not in treatment_ids:
                errors.append(f"compatibility[{index}]: unknown treatment {treatment}")
            pair = (kernel, treatment)
            if pair in compatible:
                errors.append(f"compatibility[{index}]: duplicate pair {kernel} + {treatment}")
            compatible.add(pair)

    proven_catalog = load("../catalog.json")
    proven_ids = {entry.get("recipe_id") for entry in proven_catalog.get("recipes", [])}
    for index, kernel in enumerate(kernel_rows or []):
        for recipe_id in kernel.get("recipe_refs", []):
            if recipe_id not in proven_ids:
                errors.append(f"kernels[{index}]: unknown recipe_ref {recipe_id}")

    draft_paths = sorted((V2 / "drafts").glob("*.json"))
    for path in draft_paths:
        draft = json.loads(path.read_text(encoding="utf-8"))
        if draft.get("status") != "draft":
            errors.append(f"{path}: status must be draft")
        kernel = draft.get("kernel_id")
        treatment = draft.get("treatment_id")
        profile = draft.get("profile_id")
        if kernel not in kernel_ids or treatment not in treatment_ids or profile not in profile_ids:
            errors.append(f"{path}: unknown kernel, treatment, or profile")
        if (kernel, treatment) not in compatible:
            errors.append(f"{path}: incompatible kernel/treatment")
        for field in ("source_requirements", "creative_contract", "audio_contract", "qa_contract", "promotion_gate"):
            if not isinstance(draft.get(field), list) or not draft[field]:
                errors.append(f"{path}: {field} must be non-empty")
        blueprint = draft.get("portable_blueprint")
        if blueprint and not (ROOT / blueprint).exists():
            errors.append(f"{path}: portable_blueprint does not exist: {blueprint}")
        proof = draft.get("candidate_proof")
        if proof is not None:
            if not isinstance(proof, dict):
                errors.append(f"{path}: candidate_proof must be an object")
            else:
                if proof.get("status") not in {"failed-independent-review", "accepted-first-proof", "accepted-independent-reproduction"}:
                    errors.append(f"{path}: invalid candidate_proof status")
                if not isinstance(proof.get("output_path"), str) or not proof["output_path"]:
                    errors.append(f"{path}: candidate_proof output_path is required")
                if not isinstance(proof.get("sha256"), str) or not SHA256.fullmatch(proof["sha256"]):
                    errors.append(f"{path}: candidate_proof sha256 is invalid")
                audit = proof.get("audit") or proof.get("prior_failure_audit")
                if audit and not (ROOT / audit).exists():
                    errors.append(f"{path}: candidate_proof audit does not exist: {audit}")

    validate_proposal(proposal, kernel_ids, treatment_ids, profile_ids, compatible, errors)
    router = ROOT / "skills/meta/transformation-router.md"
    if not router.exists():
        errors.append(f"missing router skill: {router}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {len(kernel_ids)} kernels, {len(treatment_ids)} treatments, {len(profile_ids)} profiles, {len(compatible)} compatible pairs, {len(draft_paths)} draft proofs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
