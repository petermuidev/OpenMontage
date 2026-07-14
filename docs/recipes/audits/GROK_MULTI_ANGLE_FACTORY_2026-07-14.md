# Grok Multi-Angle Factory Proof — 2026-07-14

## Verdict

`PASS_PROVEN_CANDIDATE`. The output is a real 15-second vertical villa reel,
not a still mockup or recipe-only claim. It remains a candidate until the owner
explicitly locks it as an accepted production pattern or baseline.

## Architecture used

- OpenMontage: source contract, shot manifest, editorial order, FFmpeg assembly,
  overlays, music, CRV, and final QA.
- Grok CLI consumer session: per-frame cleanup and image-to-video generation.
- Reasoning model: `grok-4.5` through Grok CLI `0.2.93`.
- Video model: `grok-imagine-video-1.5`, exposed by a provider `429` response.
- OpenMontage xAI API adapter: not used.
- Exact consumer-session cost: not exposed.

## Result

- Five accepted source-grounded angles from eight creative motion attempts.
- Accepted: courtyard attempt 1, master terrace attempt 2, bedroom/bath attempt
  2, cinema attempt 1, and spa attempt 1.
- Rejected: bedroom/bath attempt 1 for geometry drift, master terrace attempt 1
  for faucet/view invention, and games attempt 1 for material/geometry drift.
- Four parallel submissions returned `429` without media. They are recorded as
  harness failures, not creative attempts or paid-output claims.

The parallel failure showed that a prompt saying "sequential" is insufficient.
The harness now requires exactly one chargeable media call per headless worker
invocation, followed by review before the next submission.

## Final proof

- Local output: `projects/grok-multi-angle-villa-poc/renders/grok-multi-angle-villa-final.mp4`
- SHA-256: `193b77f7ad8fb987a61043125ffd5ba68372e4f6d99fdaecc24d8fddeab53219`
- Technical: 1080x1920, 30 fps, H.264 `yuv420p`, AAC, 15.033 seconds.
- Audio: -15.39 LUFS integrated, -2.55 dB true peak.
- QA: no black frames; eight-frame CRV and ten cut-boundary samples passed.
- Note: two locked-camera corrective shots contain short low-motion intervals;
  these were accepted to preserve property geometry and truthfulness.

Generated project media stays ignored and outside git. This audit records the
portable contract, proof path, and observed provider behavior without committing
the source or generated video.
