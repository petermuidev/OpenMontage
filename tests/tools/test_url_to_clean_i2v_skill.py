from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents/skills/url-to-clean-i2v/SKILL.md"
GUIDE = ROOT / "AGENT_GUIDE.md"
REPRO = ROOT / ".agents/skills/url-to-clean-i2v/scripts/reproduce_multishot_baseline.py"
REFERENCE = ROOT / ".agents/skills/url-to-clean-i2v/references/SAMUI_MULTISHOT_BASELINE.md"
MANIFEST = ROOT / ".agents/skills/url-to-clean-i2v/references/samui_multishot_baseline.json"


def test_skill_locks_source_cleanup_i2v_chain():
    text = SKILL.read_text()
    for required in (
        "private download and provenance",
        "face/object/text gate",
        "precise image cleanup",
        "one bounded image-to-video sample",
        "Never substitute this with",
        "explicit provider and allowed-provider list",
        "generated or reappearing person",
    ):
        assert required in text


def test_agent_guide_routes_url_transformations_to_skill():
    text = GUIDE.read_text()
    assert ".agents/skills/url-to-clean-i2v/SKILL.md" in text
    assert "Do not collapse this request into a direct recut" in text


def test_multishot_reproduction_is_documented_and_offline_only():
    assert REPRO.is_file()
    assert REFERENCE.is_file()
    manifest = MANIFEST.read_text()
    assert '"enabled_by_this_manifest": false' in manifest
    assert '"ffmpeg": "8.0.1"' in manifest
    assert '"exact_hash_scope"' in manifest
    script = REPRO.read_text()
    assert "DASHSCOPE_API_KEY" not in script
    assert "HappyHorseVideo" not in script
    assert "DashScopeWanVideo" not in script
    assert "QwenTTS" not in script
    assert "exact_baseline_match" in script
