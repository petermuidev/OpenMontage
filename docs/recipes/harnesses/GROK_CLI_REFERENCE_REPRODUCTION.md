# Grok CLI Reference-Reproduction Harness

Use this to test whether an independent Grok CLI worker can reproduce an
OpenMontage media recipe from committed documentation.

## Worker contract

Run Grok CLI headlessly with an explicit model, isolated ignored project path,
turn cap, and no subagents. The worker must read `AGENT_GUIDE.md`, analyze the
reference, validate the recipe catalog, and select a recipe from its documented
`best_for` and rejection rules.

Record:

- Grok CLI version and model.
- Reference URL and rights classification (`reference` or `source`).
- Approved production source and hash.
- Selected recipe and rejected alternatives.
- Reference-fidelity matrix: hook, shot grammar, motion, pacing, overlays, audio.
- Exact provider/tool/runtime choice and cost class.
- Output, artifacts, SHA-256, and QA result.

## Grok CLI media gate

Grok CLI login and OpenMontage xAI API configuration are different surfaces.

- `grok models` proves the CLI reasoning model is available.
- `/imagine` and `/imagine-video`, or the session's `image_edit` and
  `image_to_video` tools, prove consumer CLI media capability.
- `XAI_API_KEY` proves the separate OpenMontage API adapter is available.

Do not report “Grok video unavailable” merely because `XAI_API_KEY` is absent.
Check the CLI media surface explicitly. Conversely, do not claim the OpenMontage
API adapter is configured merely because the CLI consumer session can generate.

For a source-grounded cleanup/I2V test, use one approved extracted frame first:

1. `image_edit`: remove people, source text, logos, and unwanted objects while
   preserving real geometry, materials, perspective, lighting, crop, and view.
2. Review the full-resolution cleaned frame.
3. `image_to_video`: generate one 6-second restrained motion sample.
4. Review start, quarter, middle, three-quarter, and end frames before batching.

For multi-angle work, "sequential" is an orchestration rule, not wording inside
one worker prompt. Invoke one chargeable media generation per headless CLI run,
wait for its artifact or confirmed failure, run the shot review gate, and only
then submit the next angle. Do not place several `image_to_video` requests in one
worker task: the worker may parallelize them and trigger provider capacity limits.
Rate-limited requests that produced no media do not count as creative attempts,
but they must be recorded as harness failures.

## Mask budget

For deterministic subtitle-blur routes, calculate the **union of masked pixels**
per frame; do not sum overlapping rectangles. More than 20 percent of the frame,
or any mask over the principal subject, is a route rejection—not a creative PASS.
Select a cleaner shot/source or use precise cleanup instead. A worker may not
raise this threshold merely to make its own render pass.

Global masks are forbidden across different shot classes. Each selected interval
must have its own mask map. Moving source text requires time-bounded or keyframed
masks; if a glyph escapes a fixed mask at any reviewed frame, trim the interval or
reject the blur route.

## Dense source and final gate

Sparse midpoints do not prove a source interval or final video is clean. Before
rendering, inspect the complete source at intervals no wider than 0.5 seconds and
also inspect the exact first, last, and transition frames of every proposed shot.
Repeat the same dense review after the final encode.

The worker must emit these artifacts:

```text
source_dense_manifest
transition_frame_manifest
mask_map_per_shot
mask_union_ratio_max
full_playback_review
dense_final_review
independent_reviewer
creative_acceptance
```

`person_free=true`, `text_removed=true`, or another worker-authored Boolean is not
evidence without the corresponding frame manifest. Natural source recuts must
keep time remapping between 0.8x and 1.35x; do not stretch a short safe pocket to
hide the fact that surrounding frames are unsafe.

## Independent review

The worker cannot certify its own creative success. A separate reviewer compares:

1. output versus technical contract;
2. output versus accepted baseline;
3. output versus the declared reference-fidelity matrix;
4. output versus hard rejections and mask budget.

Classify failures as one or more of:

- `recipe-routing` — wrong recipe for the desired output;
- `recipe-contract` — missing or ambiguous gate;
- `harness` — prompt/tool/capability discovery failure;
- `worker-execution` — agent ignored a clear contract;
- `provider-quality` — generated media fails despite correct routing;
- `source-quality` — approved source cannot support the intended result.

Render success must leave `creative_acceptance=PENDING`. Only a reviewer distinct
from the producing worker may promote the reproduction result to PASS after full
playback and the dense final gate. Failed corrections remain evidence and must not
overwrite an accepted baseline or an earlier failure record.

Track tool capability and creative acceptance separately:

- `tool_capability=PASS` means the requested CLI media operation executed and
  produced a technically valid artifact.
- `creative_result=PASS` means that artifact also passes every recipe rejection,
  the accepted baseline, and the declared fidelity matrix.

`PASS_WITH_NOTES` is not a creative PASS when any note describes a hard rejection.
Examples include an invented horizon feature, boat, building, facility, furniture,
material fact, human remnant, geometry drift, or a mask that obscures the subject.
The reviewer must downgrade it to FAIL and name the failure class even when the
worker or provider labels the issue minor.

If the first cleanup fails because the provider ignores one localized removal,
do not loop the same frame indefinitely. The architect may select one materially
cleaner approved source frame and run one new bounded sample. Record the first
failure and why the replacement source lowers cleanup risk. A second failure ends
the lane until the owner changes provider or source.

Do not treat a successful cleanup as permission to accept the motion sample. Image
editing and image-to-video are separate gates. A clean still followed by invented
motion proves the CLI surface, but it does not prove a production-safe recipe.

## Capacity recovery

If Grok CLI returns a temporary `429`, preserve the session and existing outputs.
Resume by session ID with a bounded completion prompt. Do not rebuild media or
repeat a chargeable generation unless output absence is verified and the owner
approves the retry.
