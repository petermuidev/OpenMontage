# Vibe Slideshow V1 — Portable Blueprint

This blueprint transfers the `extracted-frame-slideshow-v1` kernel with the
`vibe-music-v1` treatment. Adapt the imagery, emotional arc, typography, and
motion direction to the source. Do not clone film-specific copy or colors.

## Required reading

1. `AGENT_GUIDE.md`
2. `skills/meta/transformation-router.md`
3. `docs/recipes/v2/drafts/vibe-slideshow-v1.json`
4. `pipeline_defs/cinematic.yaml` and the active stage director
5. `skills/core/hyperframes.md` plus the HyperFrames Layer 3 skills when that
   runtime is selected

## Source gate

- Authorized production source with recorded provenance.
- At least six meaningfully different, human-safe frames.
- One image strong enough to be visible on frame zero.
- No unresolved material claim, face, reflection, logo, or text.
- Build `artifacts/source_manifest.json` with the original path, SHA-256,
  dimensions, extraction time or origin, rights state, and visual role of every
  frame. Hash that manifest and use the manifest hash as the proposal source
  hash. Do not place source media in git.

Frame selection is an edit, not a sampling shortcut:

- Inspect a source contact sheet before selecting frames.
- Reject blur, near-duplicates, transition frames, bad crops, unresolved people,
  faces, reflections, third-party marks, and embedded text. For this clean-frame
  draft, media approval does not make visible URLs, watermarks, vessel text, or
  operator marks acceptable. Crop them completely, clean them with an approved
  deterministic edit, or replace the frame. Do not relabel them as source detail.
- Select a clear story role for every frame: hook, orientation, contrast,
  distinctive detail, energy change, or landing.
- Do not use two frames from the same view unless they materially change the
  story. Record that decision in `edit_decisions.json`.

## Routing gate

Write a schema-valid `artifacts/transformation_proposal.json` with exactly three
different routes. Select the slideshow only when the still inventory is stronger
than the truthful-motion inventory. Provider generation is not a default.

## Story and timing grammar

For a 15-second six-image candidate:

```text
0.0–3.0    immediate hero / location
2.4–5.4    adjacent space or experience
4.8–7.8    interior or human-scale detail
7.2–10.2   contrast in function, light, or energy
9.6–12.6  active or distinctive detail
12.0–15.0 quiet landing / strongest emotional close
```

The 0.6-second overlaps are a starting grammar, not a mandatory template. Do not
use equal scene durations unless measured music evidence supports them. Create
`artifacts/music_cue_map.json` before composition. It must record the analyzed
audio hash, selected excerpt, estimated tempo when reliable, phrase boundaries,
strong onsets, and chosen transition times. Align chosen transitions to a
recorded phrase or onset within 0.15 seconds. The opening image must be visible
at time zero; never fade up from black.

## Composition-aware motion

Choose motion from image structure:

- Strong horizon or distant view: slow push toward the horizon.
- Subject near one edge with safe negative space: restrained lateral drift.
- Strong foreground/background depth: slow push through depth.
- Dense interior requiring orientation: gentle pull back.
- Symmetrical architecture: centered push with minimal translation.
- Quiet final image: slow pull or nearly locked hold.

Keep scale approximately `1.04–1.12`; translation should normally stay within
two percent. Alternate directions only when the composition supports it. Motion
must never crop the principal room, boat, food, animal, architecture, or view.

Every visible still must move continuously for its entire scene duration. The
transform tween and opacity tweens are separate: the crossfade may finish after
0.4–0.6 seconds, but the scale/position transform must continue until that scene
leaves the screen. Never reach the final transform during fade-in and then hold.
For GSAP, the required shape is:

```js
timeline.fromTo(id, startTransform, {
  ...endTransform,
  duration: sceneDuration,
  ease: "none"
}, sceneStart);
timeline.fromTo(id, {autoAlpha: 0}, {
  autoAlpha: 1,
  duration: fadeDuration
}, sceneStart);
timeline.to(id, {
  autoAlpha: 0,
  duration: fadeDuration
}, sceneEnd - fadeDuration);
```

The first scene starts at `autoAlpha: 1`; its frame-zero visibility is mandatory.

## Design and text

Create a source-specific `DESIGN.md` before composition. Use full-frame imagery,
one restrained palette, mobile-safe typography, and no more than two primary text
moments. A persistent POC marker is required during proof work. Avoid generic
gold-luxury styling, dense cards, effect stacks, or identical motion per image.
The POC marker must already be visible on rendered frame zero. It must not fade,
slide, or animate in after time zero; animate only non-required title elements.

## Audio

- Use licensed or owner-approved music.
- Choose the music section before final timings.
- Let musical phrases and emotional energy guide the edit; do not cut
  mechanically on every beat.
- Target approximately `-18` to `-14` LUFS with no clipping.
- This treatment has no narration. Route voice-led work to the motivational or
  factual-tour treatment instead.

## Runtime

Follow the normal runtime-selection contract. HyperFrames is a strong fit for
custom HTML/GSAP motion; Remotion remains valid when its runtime is available;
FFmpeg is valid only when the approved treatment needs simple local motion. Record
every considered runtime and never swap silently.

## Required artifacts

- `transformation_proposal.json`
- `research_brief.json`
- `proposal_packet.json` and `decision_log.json`
- `script.json` (text beats even when there is no narration)
- `scene_plan.json`
- `asset_manifest.json`
- `source_manifest.json`
- `music_cue_map.json`
- `edit_decisions.json`
- `render_report.json`
- `final_review.json`
- `SHOWCASE.html`
- `reproduction_packet.json` and `worker_declaration.json` for a clean-room
  reproduction (not required for the architect proof)

Use the repository schemas for every canonical artifact.

## QA and correction cap

1. For HyperFrames 0.7.57, run `hyperframes lint`, `hyperframes validate`, and the declared
   render command; save the commands and versions in `render_report.json`.
2. Probe duration, dimensions, codec, frame rate, pixel format, and audio. A
   vertical-short proof must be 1080x1920, H.264, yuv420p, AAC, 30 fps, and
   within 0.1 seconds of its declared duration.
3. Reject any blank, black, placeholder, or title-only opening. Run FFmpeg
   `blackdetect`; no black interval longer than 0.1 seconds is permitted.
4. Run FFmpeg `freezedetect=n=0.003:d=0.8`. A slideshow proof fails when any
   visible still is effectively frozen longer than 0.8 seconds.
5. Analyze loudness. Integrated loudness must be -18 to -14 LUFS and true peak
   must not exceed -1 dBFS.
6. Run CRV with at least start, quarter, middle, three-quarter, and end coverage.
7. Review transitions and full playback, not only a contact sheet. Confirm each
   transition against `music_cue_map.json`.
8. Reject generic slideshow pacing, important-subject crops, repeated scenes,
   unsafe text, ineffective music, or unsupported claims.
9. Permit one correction render within a proof attempt. A second creative
   failure ends that attempt and must be recorded in a dated audit before a new
   proof begins.

Technical success is `first-proof` at most. Promotion requires a fresh worker to
reproduce the recipe on a different authorized source and an independent reviewer
to pass both results.

## Failure history

- `docs/recipes/v2/audits/VIBE_SLIDESHOW_PROOF_01_2026-07-14.md` records the
  rejected first proof. Its outputs are diagnostic evidence, not a baseline.
