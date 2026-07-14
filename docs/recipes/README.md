# Reusable Media Recipe Catalog

Start here when the owner asks to reproduce or adapt an earlier successful media POC.

The machine-readable index is [`catalog.json`](catalog.json). Each record names the
canonical source project, creative contract, rejection rules, proof output, and the
safe reproduction path. Run the validator before relying on it:

```bash
python3 scripts/check_media_recipe_catalog.py
python3 scripts/check_media_recipe_catalog.py --check-local-proofs
```

The second command verifies accepted output hashes when the ignored local proof
files are present. Missing ignored proof files are reported as skips, not invented
successes.

Every recipe records one concrete successful video path and SHA-256. Video files
remain in ignored local proof stores and are never committed. The portable recipe
records, schema, validation, and agent/build instructions are committed. See
[`ARTIFACT_POLICY.md`](ARTIFACT_POLICY.md).

## Status Means

| Status | Agent behavior |
|---|---|
| `accepted-baseline` | Default when its intended use matches. Preserve the proof; produce a new candidate. |
| `accepted-pattern` | Reuse the workflow and gates. Inputs and output may change. |
| `proven-candidate` | Technically and creatively complete, but ask the owner to lock it before making it the default. |
| `reference-only` | Learn from it, but do not route production to it until its missing review passes. |
| `superseded` | Do not use by default. Follow `superseded_by`. |

A rendered video is not automatically a reusable recipe. Technical QA proves the
file works; owner or independent creative review proves the pattern is worth
repeating.

## Adapt, Do Not Clone Blindly

A recipe is a reusable decision contract, not an immutable edit template. Agents
may adapt the hook, pacing, duration, scene count, language, copy, music, and
available production tool to the source and business situation. They must preserve
the recipe's intended outcome, rights and provenance checks, factual-claim limits,
hard rejections, and QA bar. An accepted proof video shows that the pattern worked
once; it does not require future work to look identical.

## Catalog Summary

As of 2026-07-14, the catalog contains **10 top-level recipes**:

| Class | Count | Meaning |
|---|---:|---|
| Accepted baselines | 3 | Locked proof outputs that control matching production |
| Accepted patterns | 3 | Reusable workflows with source-specific adaptation |
| Proven candidates | 1 | Complete, awaiting an explicit owner lock |
| Reference-only | 2 | Useful evidence, not a production route yet |
| Superseded | 1 | Preserved history; route to its successor |

That gives agents **6 production-routable recipes** today. There are also **11 named
internal deliverable blueprints**: ten inside the commercial showcase recipe and
the accepted full-frame music-recaption variant. Internal variants are not counted
again as top-level recipes.

## Routing Table

| Need | Recipe | Status |
|---|---|---|
| Ten commercial still/video formats for villas, tours, diving, food, and Samui | `face-showcase-2026-07-12` | accepted baseline |
| Owner supplies a URL; extract, remove people/text/objects, then animate | `url-to-clean-i2v-v1` | accepted pattern |
| Preserve a full vertical source frame, blur burned-in text, recaption, and add vibe music | `fullframe-source-subtitle-blur-v1` | accepted pattern |
| Short face-free, multi-shot narrated Samui reel | `samui-motivation-multishot-v1` | accepted baseline |
| Sound-off “choose 1-4” engagement post | `engagement-four-choice-v1` | accepted pattern |
| One-film emotional recommendation | `thai-film-one-thesis-editorial-v1` | accepted baseline |
| Ten films with useful three-sentence synopses | `thai-top10-three-sentence-synopsis-v1` | proven candidate |

The direct TikTok recut and three-format vibe experiments remain reference-only
because their QA reports still say visual review is pending. The short top-ten mood
picker is preserved as a specialized variant but superseded for synopsis requests.

## Universal Reproduction Rules

1. Confirm the requested outcome and select one recipe by `best_for`; do not blend
   patterns by default.
2. Resolve every `canonical_artifact` from its owning repository. `projects/` and
   `media/exports/` are ignored proof stores, not durable documentation.
3. Validate rights, claims, source identity, faces/reflections, and destination
   before creative work.
4. Copy the contract, not film-specific or operator-specific copy.
5. Render a new dated candidate. Never overwrite a locked output.
6. Run technical QA, CRV/sampled-frame review, full playback, and the recipe's
   specific creative gates.
7. Record owner disposition and output SHA before promoting a candidate.

Paid provider calls, publishing, and outreach are never implied by a recipe. The
record's `paid_calls` field describes whether reproduction can require spend; the
owner still approves each paid call.

## Promotion Rule

To promote a record, update its `status`, `proof.disposition`, QA evidence, output
path, and SHA-256, then run the validator. Never promote from technical QA alone.
