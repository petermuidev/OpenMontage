# Media Recipe Artifact Policy

The recipe catalog must survive a fresh clone without turning the repository into
a media archive.

## Commit

- `catalog.json` and every `patterns/*.json` recipe record.
- The recipe schema and catalog validator.
- Agent skills, deterministic builders, manifests, and reference JSON intended to
  reproduce a pattern.
- Human-readable design, rejection, QA, and routing documentation.

## Do Not Commit

- Successful MP4/MOV/WebM outputs.
- Downloaded source media, extracted frames, contact sheets, generated images,
  narration audio, music, intermediate segments, or CRV working directories.
- Credentials, provider task URLs, private buyer/operator evidence, or raw exports.

## Proof Contract

Every top-level recipe records exactly one representative successful video in
`proof.output_path`, names its owning repository in `proof.output_repo`, and stores
its SHA-256 in `proof.output_sha256`. The file may be ignored and local-only;
`--check-local-proofs` verifies its hash when present and reports a warning when a
fresh clone does not contain it.

HTML showcases, contact sheets, and QA reports are supporting artifacts. They do
not replace the required successful video path.

## Adaptation Contract

Recipes are starting structures. A new production may change creative variables
such as pacing, language, copy, music, scene count, or provider when the brief and
available capabilities justify it. The agent must not relax rights, truthful-claim,
face/reflection, attribution, owner-approval, or QA gates merely to match a source.

Always render to a new dated project/output path. Never overwrite the recorded
proof video.
