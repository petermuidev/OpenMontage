---
name: url-to-clean-i2v
description: Transform an owner-approved TikTok, Reel, Short, or other video URL into a face-free, source-grounded image-to-video POC. Use when a user sends a video URL and asks an agent to reuse, edit, reframe, clean, repurpose, or animate it without merely copying the clip and adding captions.
---

# URL to clean image-to-video

Treat the URL as source media only when the owner confirms reuse rights. Otherwise
analyze it as a pattern reference and use separately approved media.

## Contract

```text
approved URL
→ private download and provenance
→ source review
→ face/object/text gate
→ candidate-frame extraction
→ precise image cleanup
→ cleaned-frame QA
→ one bounded image-to-video sample
→ motion QA
→ owner approval
→ remaining variants
```

Never substitute this with “download the clip and add captions” unless the user
explicitly asks for a recut.

## Register the source

Record before editing:

```text
source_id
platform
source_url
video_id
uploader
fetched_at
rights_state
local_private_path
sha256
```

Keep downloads, cookies, tokens, and platform exports outside git. Use the
OpenMontage downloader or `yt-dlp`; do not publish or interact with the source
account.

## Review and extract

1. Probe the complete video and create a frame/contact-sheet review.
2. Reject frames containing an identifiable face, body, human silhouette, or
   human reflection when the brief requires no people.
3. Prefer scenes whose subject and geometry remain understandable as a still.
4. Extract at least three candidate frames before selecting one.
5. Store the source timestamp and frame hash for every selected image.

Do not rely on a filename or transcript to claim a frame is safe.

## Clean the frame

Use a precise-object image edit. State the edit target and invariants explicitly:

- Remove people, faces, silhouettes, reflections, embedded captions, logos,
  icons, and specifically named unwanted objects.
- Preserve the real architecture, room dimensions, pool edge, shoreline,
  horizon, furniture layout, perspective, crop, light, and material facts.
- Add no facilities, furniture, views, buildings, objects, text, or people.
- Treat cleanup as restoration, not redesign.

Inspect the result at full resolution. Reject it if a person remains or if a
material property/tourism fact changed. A second targeted cleanup may fix one
localized defect; do not endlessly regenerate a drifting scene.

## Animate the cleaned frame

Run provider preflight through `video_selector`. Announce provider, model,
duration, resolution, estimated cost, and whether the call is a sample. Use an
explicit provider and allowed-provider list so an unavailable provider cannot
silently fall back.

Generate one 3–5 second 720P sample first. For a source-grounded tourism scene:

1. Preserve the cleaned subject and geometry.
2. Request one restrained natural motion.
3. Request one restrained camera movement.
4. Repeat what must remain unchanged.
5. Exclude people, faces, silhouettes, text, logos, new objects, warping, and
   scene replacement.

Use a fixed seed when supported. Persist a task ID before polling. If submission
times out without a task ID, report financially uncertain state and do not
blindly batch. If a provider is unpurchased, unavailable, or unhealthy, stop and
request approval before switching providers or using a still-animation fallback.

## Motion QA

Watch the whole sample and inspect start, 25%, 50%, 75%, and end frames. Reject:

- any generated or reappearing person, face, silhouette, or reflection;
- geometry drift, moving architecture, changed room or pool dimensions;
- invented facilities, furniture, boats, animals, text, or logos;
- implausible water, vegetation, horizon, lighting, or camera motion;
- blank openings/endings or frozen output.

The generated motion is a creative POC, not evidence that the operator or place
behaved that way.

Treat provider or worker `PASS_WITH_NOTES` as FAIL whenever a note matches one of
the rejection conditions above. Record tool execution separately from creative
acceptance: a provider can prove that image-to-video is callable while its output
still fails the source-grounded tourism contract. Do not soften an invented
horizon object, furniture morph, or changed facility to “minor” for promotion.

## Lock the reusable recipe

For each accepted pattern, save:

```text
pattern_id
source_contract
frame_selection_rule
cleanup_prompt
cleanup_invariants
i2v_provider
i2v_model
i2v_prompt
duration
resolution
seed
cost
source_hash
clean_frame_hash
output_hash
qa_disposition
```

Only mark the pattern reusable after the cleaned image and generated-motion
sample both pass. Do not equate a technical render with creative acceptance.

## Multi-shot narration baseline

When the output is a narrated multi-shot engagement edit, compare it with the
owner-accepted baseline at:

```text
projects/samui-clean-i2v-pocs/artifacts/BASELINE_LOCK.json
```

For a comparable ten-second edit, require four meaningful visual shots, align
cuts to real narration pauses, keep music below the voice, and use only voices
explicitly supported by the selected TTS model. A new render may improve the
baseline, but it cannot silently lower its visual diversity, readability,
factual safety, or audio clarity.

Read `references/SAMUI_MULTISHOT_BASELINE.md` for the accepted proof and run
`scripts/reproduce_multishot_baseline.py --check` before claiming the lane is
reproducible. The script recomposes accepted local artifacts only; it cannot
call paid providers.
