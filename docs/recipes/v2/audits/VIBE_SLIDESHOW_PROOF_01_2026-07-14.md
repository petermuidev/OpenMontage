# Vibe Slideshow Proof 01 — Rejected

Date: 2026-07-14

This proof attempted to validate `vibe-slideshow-v1` using six owner-approved
villa frames. It is retained as failure evidence and must not be presented as a
successful example or creative baseline.

## Attempt history

1. `vibe-slideshow-proof-v1.mp4` was rejected because it opened on black.
2. `vibe-slideshow-proof-v2.mp4` fixed frame-zero visibility but failed
   independent creative review.

The second output passed container, resolution, codec, audio, and sampled-frame
checks. That technical success did not make it creatively acceptable.

## Independent-review failure

Scenes two through six completed their scale and position movement during the
0.58-second fade-in and then held the same transform for approximately 1.9
seconds. FFmpeg `freezedetect=n=0.003:d=0.8` identified long holds around:

```text
2.90–4.83
5.27–7.23
7.73–9.63
10.13–12.03
12.70–14.57
```

The cut spacing was also uniform without an artifact proving that those cuts
followed the selected music. The result read as a generic slideshow rather than
a composition-aware music edit.

## Root cause and contract correction

- Transform and fade animations were coupled; the transform reached its final
  state during the fade instead of continuing throughout the visible scene.
- The recipe asked for musical phrasing but did not require a measured cue map.
- The recipe lacked an objective freeze threshold.
- Frame provenance was described but not enforced as a hashed manifest.

The portable blueprint now requires separate full-duration transform tweens,
`music_cue_map.json`, source-manifest hashing, black/freeze thresholds, and
explicit technical targets. A new proof must follow the amended contract from
scratch. Neither rejected render satisfies the promotion gate.
