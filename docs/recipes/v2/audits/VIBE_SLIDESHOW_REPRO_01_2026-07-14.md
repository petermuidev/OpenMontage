# Vibe Slideshow Independent Reproduction 01 — First Candidate Rejected

Date: 2026-07-14

Candidate `vibe-slideshow-independent-repro-v1.mp4` proved that a fresh worker
could independently route, design, compose, and render the slideshow, but it did
not satisfy the full recipe contract.

## Passed

- Different owner-approved source set.
- Independent phrase/onset map and scene timing.
- HyperFrames lint/runtime validation.
- 1080x1920, H.264/yuv420p, AAC, 30 fps, 15.04 seconds.
- No black or freeze intervals; loudness within target.
- Continuous motion, distinct scenes, safe main titles, and zero provider spend.

## Rejected

1. The boat scene retained a visible operator URL, branding, and vessel text.
   Owner-approved media did not satisfy this draft's clean-frame requirement.
2. The persistent POC marker faded in after time zero and was absent on the saved
   start frame.
3. The project did not include a pre-work reproduction packet or worker
   declaration, so clean-room separation was not auditable inside the package.
4. The execution report incorrectly described HyperFrames as assigned rather
   than selected after the worker's runtime preflight.

This candidate is not a successful reproduction. One correction render is
permitted: replace the marked boat frame, make the POC marker visible at frame
zero, correct the runtime record, and add truthful separation artifacts. The
corrected candidate still requires independent review.
