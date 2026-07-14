# Independent Recipe Reproduction Harness

Use this harness to determine whether a recipe is portable to another LLM agent.

## Separation contract

- The architect supplies only the repository path, recipe or draft ID, approved
  source paths with rights evidence, output project name, and spend cap.
- The worker receives no source-specific HTML, prompts, timeline, or private chat
  explanation from the architect's first proof.
- The worker reads the router, selected blueprint, pipeline, director skills, and
  tool skills from the repository.
- The worker writes only to its assigned ignored `projects/<name>/` directory.
- The worker must not edit catalogue, recipe, pipeline, or tool files.
- Paid or stochastic calls remain blocked unless the owner separately approves.

Before the worker starts, save the exact assignment as
`artifacts/reproduction_packet.json`. It records the worker/session ID, start
time, recipe ID, approved source and audio paths, rights evidence, output
directory, spend cap, prohibited prior-proof paths, allowed correction count,
and the exact instructions. Runtime must be `worker-selected`; the architect may
state availability constraints but must not preselect a compositor or timeline.

## Worker deliverables

1. Schema-valid transformation proposal with three routes.
2. Explicit route and runtime decision log.
3. Complete pipeline artifact set required by the blueprint.
4. Candidate video, showcase, provenance, SHA-256, and QA report.
5. A short execution report naming unclear, missing, or contradictory guidance.
6. `worker_declaration.json` naming every recipe/pipeline/tool document read,
   declaring whether any prohibited prior proof was inspected, recording the
   runtime decision, and linking the immutable reproduction packet.

The worker may ask the architect only when a rights, spend, provider, or major
runtime decision cannot be resolved from the assigned packet. Creative adaptation
within the selected recipe is the worker's responsibility.

## Independent review

A separate reviewer receives the blueprint, source, artifacts, and output. It
classifies findings as:

- `recipe-routing`
- `recipe-contract`
- `worker-execution`
- `provider-quality`
- `source-quality`
- `composition-tooling`
- `qa-tooling`

The reviewer does not repair the output or silently edit the recipe. It returns
`PASS` or `FAIL`; any blueprint hard rejection forces `FAIL`.

## Promotion

`first-proof → independently-reproduced` requires:

- a different authorized source;
- no private architect instructions;
- an auditable reproduction packet created before work and a matching worker
  declaration;
- all required artifacts;
- no more than one correction render;
- independent creative and technical PASS.

Owner acceptance remains a separate promotion gate after reproduction.
