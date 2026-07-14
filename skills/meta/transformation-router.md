# Transformation Router — Meta Skill

Use this skill after a user supplies a video URL, local video, or approved media
and asks what it can become. This skill chooses a production route; it does not
render, publish, spend, or bypass a pipeline.

## Required inputs

1. Classify the input as `reference`, `authorized-source`, or
   `reference-with-separate-sources`.
2. Resolve rights before treating visible media as a production source.
3. Run the appropriate reference analysis or source-media review.
4. Record duration, usable intervals, distinct scenes, extractable frames,
   people/faces/reflections, text/logos, audio state, and verified facts.

Unknown rights, unknown facts, or unreadable media are routing blockers, not
permission to guess.

## Catalogue loading

Read:

1. `docs/recipes/v2/kernels.json`
2. `docs/recipes/v2/treatments.json`
3. `docs/recipes/v2/delivery_profiles.json`
4. `docs/recipes/v2/compatibility.json`

Then produce exactly three differentiated candidates. Each candidate selects one
kernel, one treatment, one delivery profile, and one pipeline. Compatibility is
reject-by-default. A conditional rule must list its unsatisfied gates.

Rank candidates using grounded judgment:

1. Truth and rights safety.
2. Source support for the requested story.
3. Expected creative quality.
4. Execution reliability and speed.
5. Cost.

Prefer truthful real-media transformation over generated reconstruction whenever
both can meet the brief. Do not recommend a complex route merely because the tool
exists.

## Artifact

Write `artifacts/transformation_proposal.json` following
`docs/recipes/v2/transformation-proposal.schema.json`. Before production, present
the three routes with their quality potential, truth risk, cost class, gates, and
likely failures. Recommend one, then wait for owner selection when the choice
changes provider, spend, source mode, narration, or composition character.

After selection, load only:

- the selected kernel record;
- the selected treatment record;
- the selected delivery profile;
- referenced proven recipe when one exists;
- the selected pipeline manifest and current stage director.

Do not blend several kernels by default. If the source genuinely needs a hybrid,
one kernel remains primary and every supporting operation must be named in the
decision log.

## Rejections

- Three cosmetic variations of the same route.
- Treating a reference URL as authorized footage.
- Recommending human removal from moving video when clean cuts or frame cleanup
  are the safer route.
- Generated rooms, views, facilities, conditions, or availability presented as
  documentary evidence.
- A narration plan without sentence-to-scene support.
- A treatment/kernel pair absent from the compatibility file.
- Paid or stochastic generation before owner approval.
- Calling a draft recipe accepted because it rendered once.

