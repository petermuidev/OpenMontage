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
