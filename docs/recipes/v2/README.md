# Media Transformation Catalogue V2

This directory adds a decision layer above the proven recipe catalogue. It does
not replace `docs/recipes/catalog.json` and does not turn unproven combinations
into production defaults.

```text
source or reference
→ transformation proposal
→ one kernel + one treatment + one delivery profile
→ compatible OpenMontage pipeline
→ recipe-specific production and QA
```

## Files

- `kernels.json`: truth and technical transformation methods.
- `treatments.json`: story and audio treatments that may modify a kernel.
- `delivery_profiles.json`: output dimensions and duration contracts.
- `compatibility.json`: explicit allowed or conditional kernel/treatment pairs.
- `transformation-proposal.schema.json`: per-source routing artifact contract.
- `examples/`: schema-valid routing examples, not production approvals.
- `drafts/`: proof contracts that are not yet part of the proven catalogue.
- `blueprints/`: portable production contracts for a specific draft.
- `audits/`: accepted and rejected proof evidence; failures are never baselines.
- `harnesses/`: clean-room reproduction contracts for another agent.
- `PHASE_PLAN.md`: ordered implementation and promotion plan.

The compatibility default is reject. A pair is usable only when an explicit rule
marks it `allowed` or `conditional`, and conditional gates must be satisfied.

Agents must read `skills/meta/transformation-router.md`, then load only the
selected kernel, treatment, delivery profile, pipeline, and recipe. Do not load or
blend the complete catalogue into every production prompt.

Validate without rendering or provider calls:

```bash
python3 scripts/check_media_transformation_catalog.py
```

## Why this is broad without becoming recipe sprawl

The reusable unit is not a finished video template. A source transformation
kernel answers what may truthfully happen to the media; a treatment answers how
the result communicates; a delivery profile answers where it must work. The
explicit compatibility table controls which combinations may be attempted.

The director adapts story, shot order, crop, motion, typography, language, and
audio to the source. It does not clone the proof's copy, color, or timeline.
Only the hard truth, provenance, runtime, artifact, and QA contracts transfer.
