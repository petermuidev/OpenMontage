import subprocess
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_media_recipe_catalog_contract() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_media_recipe_catalog.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "11 media recipes validated" in result.stdout


def test_every_recipe_names_a_hashed_video_proof() -> None:
    catalog = json.loads((ROOT / "docs/recipes/catalog.json").read_text())
    for entry in catalog["recipes"]:
        recipe = json.loads((ROOT / "docs/recipes" / entry["record"]).read_text())
        proof = recipe["proof"]
        assert proof["output_repo"] in {"openmontage", "face"}
        assert proof["output_path"].lower().endswith((".mp4", ".mov", ".webm"))
        assert len(proof["output_sha256"]) == 64


def test_fullframe_cleanup_recipe_requires_dense_independent_review() -> None:
    recipe = json.loads(
        (
            ROOT
            / "docs/recipes/patterns/fullframe-source-subtitle-blur-v1.json"
        ).read_text()
    )
    contract = " ".join(
        recipe["source_contract"]
        + recipe["creative_contract"]
        + recipe["qa_contract"]
    ).lower()
    assert "0.5 seconds" in contract
    assert "union of masked pixels" in contract
    assert "global mask" in contract
    assert "0.8x and 1.35x" in contract
    assert "reviewer distinct from the producing worker" in contract
    assert "sparse midpoint" in contract
