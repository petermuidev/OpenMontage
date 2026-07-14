# Samui narrated multi-shot baseline

This is the first owner-accepted baseline for the URL → clean frames → I2V →
multi-shot narration lane.

## What is reproducible

The accepted local motion shots, narration, music, overlays, timing, mix, and
final encode can be recomposed without network access or provider spend:

```bash
.venv/bin/python .agents/skills/url-to-clean-i2v/scripts/reproduce_multishot_baseline.py --check
.venv/bin/python .agents/skills/url-to-clean-i2v/scripts/reproduce_multishot_baseline.py --compose
```

The default compose destination is under the ignored project `.work/` folder.
It never overwrites the accepted master.

Run QA on either the accepted master or a reproduced file:

```bash
.venv/bin/python .agents/skills/url-to-clean-i2v/scripts/reproduce_multishot_baseline.py --qa-only
.venv/bin/python .agents/skills/url-to-clean-i2v/scripts/reproduce_multishot_baseline.py --qa-only --output /absolute/path/to/reproduction.mp4
```

## What is not bit-reproducible

Image cleanup, HappyHorse/Wan motion generation, and Qwen speech synthesis are
model calls. Seeds and prompts provide provenance, not a guarantee of identical
pixels or audio. Those stages are paid/stochastic regeneration and require a
new owner approval. The reproduction script cannot invoke them.

## Agent order

1. Read `../SKILL.md`.
2. Run `--check`; do not repair missing inputs by substitution.
3. Read `samui_multishot_baseline.json` and the local `BASELINE_LOCK.json`.
4. Run `--compose` to prove deterministic assembly.
5. Run `--qa-only` and compare the reported specifications and hash.
6. Only propose paid regeneration if the owner asks for new motion or voice.

The accepted master is local/ignored media. A clean clone has the recipe but
must receive the approved source artifacts before composition can pass.
Use `--project-root /absolute/path/to/the/restored/asset/root` after that asset
bundle is restored. Never replace a missing hash-pinned asset with a public URL,
lookalike image, regenerated clip, or different music track.

Exact byte-for-byte reproduction is proven for Python 3.12.13, Pillow 12.3.0,
and FFmpeg 8.0.1 on this macOS arm64 host. Another supported toolchain must pass
technical and visual QA, but must not claim an exact hash match unless it
actually produces the locked SHA-256.
