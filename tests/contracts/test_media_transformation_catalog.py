import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_media_transformation_catalog_contract() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_media_transformation_catalog.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "7 kernels, 10 treatments, 6 profiles" in result.stdout


def test_drafts_do_not_enter_proven_recipe_catalog() -> None:
    catalog = json.loads((ROOT / "docs/recipes/catalog.json").read_text())
    recipe_ids = {entry["recipe_id"] for entry in catalog["recipes"]}
    for draft_path in (ROOT / "docs/recipes/v2/drafts").glob("*.json"):
        draft = json.loads(draft_path.read_text())
        assert draft["status"] == "draft"
        assert draft["draft_id"] not in recipe_ids
