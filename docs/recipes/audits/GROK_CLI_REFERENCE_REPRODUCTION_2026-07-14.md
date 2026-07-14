# Grok CLI Reference-Reproduction Audit — 2026-07-14

## Decision

Grok CLI consumer-session media tools are **capable but not yet promoted as a
source-grounded production route**.

| Gate | Result | Evidence |
|---|---|---|
| Grok CLI reasoning worker | PASS | Read the committed catalog, analyzed the reference and source, selected a recipe, rendered, and wrote provenance/QA artifacts |
| Deterministic reference reproduction | FAIL | Broad subtitle blur bands dominated the villa composition and missed the reference's clean reveal grammar |
| Native `image_edit`, sample 1 | FAIL | Removed text but retained the explicitly targeted small animal |
| Native `image_edit`, sample 2 | PASS | Removed Chinese/English overlays from a materially cleaner owner-approved courtyard frame |
| Native `image_to_video`, sample 2 | FAIL | Invented a dark island/boat-like horizon feature and introduced slight furniture drift |
| Overall production promotion | FAIL | Tool capability is proven; source-grounded creative reliability is not |

The ignored local audit project is:

```text
projects/grok-cli-trulyworthit-reproduction-poc/
```

Key local evidence:

```text
outputs/trulyworthit-style-villa-poc-v1.mp4
outputs/grok-native-clean-courtyard-i2v-6s-v1.mp4
artifacts/QA_REPORT.json
artifacts/GROK_NATIVE_MEDIA_REPORT.json
artifacts/GROK_NATIVE_MEDIA_REPORT_2.json
assets/grok-native/crv-independent/grids/grid_01.jpg
assets/grok-native/crv-independent/grids/grid_02.jpg
```

The reference TikTok was used only for visual grammar. Production used separately
approved owner media.

## What the worker and docs got wrong

1. The first worker optimized for removing source overlays, so it selected the
   full-frame blur recipe even though the target reference used a clean,
   unobstructed architectural reveal.
2. The accepted blur recipe did not quantify how much of a frame could be masked,
   allowing technically hidden text to be mistaken for creative success.
3. The native media worker correctly reported `PASS_WITH_NOTES`, but described an
   invented horizon feature as minor. That note matches the source-grounded
   recipe's hard rejection and therefore cannot be promoted.
4. Tool availability, cleanup success, and motion success were not separated
   strongly enough. They are now three independent gates.

## Corrections locked by this audit

- Classify every URL as `reference` or authorized `source` before routing.
- Write a reference-fidelity matrix before production.
- Reject deterministic blur when combined masks exceed 20 percent or hide the
  principal subject.
- Keep `tool_capability` and `creative_result` verdicts separate.
- Downgrade any `PASS_WITH_NOTES` whose notes match a hard rejection.
- Gate cleaned-frame acceptance separately from motion acceptance.
- Permit only one materially cleaner corrective source after a localized cleanup
  failure; stop after the second failed creative sample.

## Routing result

- Continue using HappyHorse as the quality I2V lane already accepted by the owner.
- Continue using Wan Flash only for restrained still-animation inside a larger
  composition.
- Keep Grok CLI useful for analysis, frame cleanup candidates, and bounded media
  experiments, but require independent review for every generated shot.
- Do not batch Grok I2V for truthful villa/tour inventory until a new bounded
  sample passes without invented objects, views, or geometry drift.
